import threading
from time import time
from WebSocketServer.WSFrame import WebSocketOutput
import pdb

# an anonymous thread started for every client which sends ping requests
# currently unused
# class PingThread(threading.Thread):
	# def __init__(self, channel):
		# self.channel = channel
		# self.pingas = 0
		# self.lastPing = int(time())
		# threading.Thread.__init__ ( self )
	
	# def run(self):
		# global PING_EVERY
		# while True:
			# now = int(time())
			# if (now - self.lastPing) >= PING_EVERY:
				# try:
					# self.pingas += 1
					# #print 'Ping', self.pingas, self.channel.getpeername(), now
					# self.channel.send(WebSocketPing(['0x89','0x21','0xa7','0x4b'], now)) # arbitrary key
					# self.lastPing = now
				# except:
					# break

# thread to send messages to the connected client in LIFO way
class MsgThread(threading.Thread):
	def __init__(self, channel):
		self.channel = channel
		self.msgCount = 0
		self.outbox = []
		self.running = True
		threading.Thread.__init__ ( self )
	
	def updateKey(self, maskKey):
		self.mask = False #maskKey #Override: Server-to-Client frames MUST NOT be masked
	
	def close(self):
		self.running = False
	
	def send(self, encodedMsgData):
		self.outbox.append(encodedMsgData)
		self.msgCount += 1
	
	def run(self):
		while self.running:
			try:
				msg = self.outbox.pop()
				# if hasattr(msg, 'sendAt'):
					# if msg.sendAt == int(time()):
						# out = WebSocketOutput(msg.text(), self.mask)
						# self.channel.send(out.encode())
					# elif msg.sendAt > int(time()):
						# self.outbox.append(msg) # goes back to the beggining so its popped at the next try. this means there can only be one timed msg in a thread
				# else:
				out = WebSocketOutput(msg.text(), self.mask)
				self.channel.send(out.encode())
			except IndexError:
				pass
			except:
				pass