import SocketServer
import json
import threading
import socket

from WebSocketServer.WSConnectionHandler import *
from WebSocketServer.WSClient import *
#from WebSocketServer.WSHelperThreads import PingThread

PORT = 8000
PING_EVERY = 10 # TODO reinstate pings with this value?
# TODO command types: as broadcast; listening as in waits for reply and resubmission is blocked by client
# TODO check if name already exists

cPool = ClientPool()

import pdb # TODO remember to remove all references to this when completing the stage
# TODO after the game is completed
# TODO handle opponent disconnection during challenge


class ClientHandler(WSConnectionHandler):
	# new connection
	def setup(self):
		global cPool
		self.c = Client(self.client_address, cPool, self.request)
		cPool.add(self.c)
		print "Connection established to", self.client_address, "Client ID:", self.c.id
		#PingThread(self.request).start()
	
	# connection lost
	def finish(self):
		global cPool
		
		# stop outbox thread and wait for it to finish
		self.c.mthread.close()
		while self.c.mthread.isAlive():
			pass
		
		# inform other users
		for agent in cPool.clients:
			if agent.id != self.c.id:
				agent.outbox({'cmd':'drop','id':self.c.id})
		
		print "Connection lost to", self.client_address, "Client ID:", self.c.id
		
		# remove from client pool
		self.c.log('Client disconnected')
		cPool.remove(self.c)
		
		# delete object
		del self.c
	
	# handle client message data
	def handleMsg(self, clientFrame):
		global cPool
		# process incoming messages
		self.c.mthread.updateKey(clientFrame.maskHex)
		clientMsg = clientFrame.payload
		try:
			pMsg = json.loads(clientMsg)
		except ValueError:
			self.c.log('ERROR: Unparsable client message')
		else:
			if clientFrame.opcode == 'text':
				msg = Msg(pMsg)
				msg.raw['from'] = self.c.id
				self.c.inbox(msg) # even (especially) if broadcast, this has to be processed first for originating client
				if msg.broadcast:
					for agent in cPool.clients:
						if agent.id != self.c.id:
							agent.inbox(msg)
			elif clientFrame.opcode == 'pong':
				self.c.log('Pong ' + clientMsg)

# this makes sure the tcp server is threaded
class LoginServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass

server = LoginServer(("", PORT), ClientHandler)
print "serving at port", PORT
server.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
try:
	print "TCP_NODELAY = ", server.socket.getsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY) #TODO
	#print "TCP_CORK = ", server.socket.getsockopt(socket.IPPROTO_TCP, socket.TCP_CORK) #TODO
	# http://www.techrepublic.com/article/tcpip-options-for-high-performance-data-transmission/1050878
except:
	pass

server_thread = threading.Thread(target=server.serve_forever)
server_thread.daemon = True
server_thread.start()

#cpu_client = CPUClient(PORT)

while server_thread.isAlive():
	pass

server.shutdown()