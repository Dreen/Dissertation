from time import time

class Game:
	def __init__(self, gameID, poolRef):
		self.gameID = gameID
		self.players = {'left':False,'right':False}
		self.cPool = poolRef
	
	def addPlayer(self, side, id):
		self.players[side] = self.cPool.getById(id)
		self.players[side].log('Added to game '+self.gameID)
		
		# if all players are ready, start the game
		if self.isReady():
			for side in self.players:
				self.players[side].opponent = self.players['right' if side=='left' else 'left']
				self.players[side].outbox({'cmd':'start'})
				self.players[side].log('Starting the game')
	
	def isReady(self):
		for side in self.players:
			if not self.players[side]:
				return False
		return True
	
	# def countdown(self):
		# for i in range(4,-1,-1):
			# for side in self.players:
				# self.players[side].outbox({'cmd':'cdup','stage':i,'sendAt':int(time())+(5-i)})
				# self.players[side].log('Game starting in ' + str(i))