from WebSocketServer.WSHelperThreads import MsgThread
from WebSocketServer.WSClient import *
from WebSocketGame.Game import *

import pdb

BROADCAST_COMMANDS = [] # DOES NOT SUPPORT BROADCAST SINCE VIRTUAL CONNECTION IS ONLY BETWEEN TWO CLIENTS ATM
# PLAYER_CMD = {
# 'MOVE_NORTH' = 'w',
# 'MOVE_EAST' = 'd',
# 'MOVE_SOUTH' = 's',
# 'MOVE_WEST' = 'a'
# }
CONTROLS = ['w','d','s','a']

class Player(Client):
	def __init__(self, client, poolRef, channel):
		# properties
		self.client = client
		
		# resources
		self.out = False
		self.cPool = poolRef
		self.channel = channel
		self.mthread = MsgThread(self.channel)
		self.mthread.start()
	
	def inbox(self, inMsg):
		if self.out: # TEMP FIX TODO output isnt open yet, use a buffer which is then loaded after registering
			self.log('> ' + inMsg.text())
		if inMsg.cmd:
			# Register new user
			if inMsg.cmd == 'reg':
				self.id = inMsg.raw['playerID']
				
				self.out = open('game_logs/' + self.id + '.log','a')
				self.log("New client registered: " + ":".join(map(str,self.client)) + ' ID is: ' + self.id)
				self.mthread.setName('MsgThread ' + self.id)
				
				# Add player to the game.
				self.cPool.newGame(inMsg.raw['challengeID'])
				self.cPool.games[inMsg.raw['challengeID']].addPlayer(inMsg.raw['playerSide'], self.id)
				return
			
			# User requests a countdown reset
			# if inMsg.cmd == 'resetCountdown':
				# game = self.cPool.games[inMsg.raw['challengeID']]
				# self.log('Countdown reset requested for game ' + game.gameID + ' by '+self.id)
				# for s in game.players:
					# game.players[s].mthread.outbox = []
					# game.players[s].outbox({'cmd':'resetCountdown'})
				# game.countdown()
				# return
			
			if inMsg.cmd in CONTROLS:
				self.log(inMsg.cmd)
				self.opponent.outbox(inMsg.raw)
				return
		
		# If we're here, the message is invalid
		self.invalidMsg(inMsg)

# This class aggregates all players currently connected to the server,
# as well as keeping track of active games
class PlayerPool(ClientPool):
	def __init__(self):
		self.clients = []
		
		# a dict holding games
		self.games = {}
		# useless in GameServer but keeping for compliance with getById
		self.aliases = {}
	
	def add(self, client):
		self.clients.append(client)
	
	def newGame(self, challengeID):
		if challengeID not in self.games:
			self.games[challengeID] = Game(challengeID, self)