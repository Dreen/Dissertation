from time import time, strftime, localtime
from hashlib import md5
from os import remove, listdir
import json

from WebSocketServer.WSHelperThreads import MsgThread

import pdb

BROADCAST_COMMANDS = ['msg','reg','drop','challenge','challengeResponse', 'challengeReady']
#LISTENING_COMMANDS = ['reg','list','challenge']

class Client:
	def __init__(self, client, poolRef, channel):
		# properties
		self.username = ''
		self.client = client
		self.joined = int(time())
		self.id = md5(":".join(map(str, self.client))+':'+str(self.joined)).hexdigest()[0:16]
		# TODO make sure ID is unique ? 
		
		# resources
		self.out = open('client_logs/' + self.id + '.log','w')
		self.cPool = poolRef
		self.channel = channel
		self.mthread = MsgThread(channel)
		self.mthread.setName('MsgThread ' + self.id)
		self.mthread.start()
		
		self.log("New client: " + ":".join(map(str,self.client)) + ' (id:' + self.id + ')')
	
	def switchIdentity(self, newID):
		oldID = self.id
		# change id, out, cPool, mthread name
		self.id = newID
		self.out.close()
		remove('client_logs/' + oldID + '.log')
		self.out = open('client_logs/' + self.id + '.log','a')
		self.cPool.idFileList.remove(oldID)
		self.cPool.aliases[oldID] = self.id
		self.mthread.setName('MsgThread ' + self.id)
		
		self.log("Restored session. Client: " + ":".join(map(str,self.client)))
	
	def log(self, msg):
		msg = msg.encode('utf-8')
		self.out.write(strftime("[%H:%M:%S] ", localtime()) + msg + "\n")
		self.out.flush()
	
	def setName(self, uname):
		self.log("Registered as " + uname)
		self.username = uname
	
	# if we want to expand for other data formats do it here
	def outbox(self, rawMsgData):
		msg = Msg(rawMsgData)
		self.log('< ' + msg.text())
		self.mthread.send(msg)
	
	def invalidMsg(self, inMsg):
		self.log('Invalid message: ' + inMsg.text())
		self.outbox({'cmd':'err','errstr':'Invalid message'})
	
	def inbox(self, inMsg):
		self.log('> ' + inMsg.text())
		if inMsg.cmd:
			# Register new user
			if inMsg.cmd == 'reg':
				if inMsg.raw['from'] == self.id:
					self.setName(inMsg.raw['reg'])
					# you've been here before, lets restore your session
					if 'prevID' in inMsg.raw and inMsg.raw['prevID'] in self.cPool.idFileList:
						self.switchIdentity(inMsg.raw['prevID'])
						self.outbox({'cmd':'hi','id':self.id,'wb':'True'})
					# welcome new user
					else:
						self.outbox({'cmd':'hi','id':self.id})
				else:
					user = self.cPool.getById(inMsg.raw['from'])
					self.outbox({'cmd':'new','id':user.id,'username':user.username})
				return
				
			# Request for listing of registered users
			elif inMsg.cmd == 'list':
				tmp = {'cmd':'listres','userlist':[]}
				for user in self.cPool.clients:
					tmp['userlist'].append([user.id, user.username])
				self.outbox(tmp)
				return
				
			# A message from user
			elif inMsg.cmd == 'msg':
				if inMsg.raw['from'] != self.id:
					self.outbox(inMsg.raw)
				return
			
			# User pressed the disconnect button
			elif inMsg.cmd == 'drop':
				#self.channel.close()
				self.log('Disconnected')
				# if inMsg.raw['from'] != self.id:
					# self.outbox({'cmd':'drop','id':inMsg.raw['from']})
				return
			
			# User challenged someone to a fight
			elif inMsg.cmd == 'challenge':
				if self.id == inMsg.raw['opponent']:
					# TODO <do something here?> challenge initiated, waiting for response
					self.outbox({'cmd':'challenge','opponent':inMsg.raw['from']})
				# TODO <do something here?> elif inform others of a strated challenge?
				return
			
			# User responds to a challenge
			elif inMsg.cmd == 'challengeResponse':
				if self.id == inMsg.raw['opponent']:
					if not ('response' in inMsg.raw):
						self.invalidMsg(inMsg)
					else:
						inMsg.raw['opponent'] = inMsg.raw['from']
						del inMsg.raw['from']
						if inMsg.raw['response'] == 'accept':
							inMsg.raw['challengeID'] = self.cPool.newChallenge(inMsg.raw['opponent'], self.id)
							self.cPool.getById(inMsg.raw['opponent']).outbox({'cmd':'challengeID','opponent':self.id,'challengeID':inMsg.raw['challengeID']})
						self.outbox(inMsg.raw)
				return
			
			# User indicates readiness to start the game
			elif inMsg.cmd == 'challengeReady':
				if self.id == inMsg.raw['opponent']:
					inMsg.raw['opponent'] = inMsg.raw['from']
					del inMsg.raw['from']
					self.outbox(inMsg.raw)
				return
			
		# If we're here, the message is invalid
		self.invalidMsg(inMsg)

# This class aggregates all clients currently connected to the server,
# as well as keeping track of active challanges
class ClientPool:
	def __init__(self):
		self.clients = []
		self.idFileList = []
		for idFile in listdir('client_logs'):
			self.idFileList.append(idFile.replace('.log',''))
		
		# a dict holding challenges
		# challengeID = challengerID+challengeeID
		# challenges[challengeID] = [Client(challenger),Client2(challengee)]
		self.challenges = {}
		
		# a dict holding ids which existed only a second before changing identity. req to make getById work correctly
		self.aliases = {}
	
	# def dump(self):
		# for i in range(len(self.clients)):
			# print i, self.clients[i].id, self.clients[i].username, len(self.clients[i].mthread.outbox)
	
	def add(self, client):
		self.clients.append(client)
		self.idFileList.append(client.id)
	
	def remove(self, client):
		client.log("Removing from pool")
		try:
			self.clients.remove(client)
		except ValueError:
			client.log("... Failed, not in pool")
			return False
		else:
			return True
	
	def getById(self, id):
		if id in self.aliases:
			id = self.aliases[id]
		for i in range(len(self.clients)):
			if self.clients[i].id == id:
				return self.clients[i]
		return False
	
	def newChallenge(self, p1, p2):
		id = p1+p2
		self.challenges[id] = [self.getById(p1), self.getById(p2)]
		return id

class Msg:
	def __init__(self, input):
		# if 'sendAt' in input:
			# self.sendAt = int(input['sendAt'])
			# del input['sendAt']
		self.raw  = input
		self.cmd  = input['cmd'] if 'cmd' in self.raw else False
		self.broadcast = self.cmd in BROADCAST_COMMANDS
	
	def text(self):
		return json.dumps(self.raw)

# pdb.set_trace()
# a = Client(['127.0.0.3',6663])
# pool = ClientPool()
# pool.add(Client(['127.0.0.1',6661]))
# pool.add(Client(['127.0.0.2',6662]))
# pool.add(a)
# pool.add(Client(['127.0.0.4',6664]))
# b = pool.getById(a.id)
# pool.remove(a)
# pass