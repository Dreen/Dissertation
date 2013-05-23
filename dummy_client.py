import socket
import json
import threading
import sys
from time import time, sleep
from random import randint as rand

from WebSocketServer.WSFrame import *

class InThread(threading.Thread):
	def __init__(self, channel):
		self.channel = channel
		self.running = True
		threading.Thread.__init__ ( self )
		
	def run(self):
		while self.running:
			try:
				self.channel.recv(1024)
			except:
				pass
		# data = self.client.recv(1024).strip()
		# inm = WebSocketInput(data)
		# #print '>', inm.opcode, inm.payload
		# if inm.opcode == 'ping':
			# self.wspong()

class OutThread(threading.Thread):
	def __init__(self, channel):
		self.channel = channel
		self.running = True
		self.outbox = []
		threading.Thread.__init__ ( self )
	
	def send(self, jsonMsg):
		self.outbox.append(WebSocketOutput(json.dumps(jsonMsg), map(hex,[137, 42, 167, 75])).encode())
	
	def run(self):
		while self.running:
			try:
				msg = self.outbox.pop()
				self.channel.send(msg)
			except:
				pass

class DummyClient(threading.Thread):
	def __init__(self, number):
		self.running = False
		self.registered = False
		self.connected = False
		self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.client.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
		#self.client.connect(('192.168.1.75',8000))
		self.client.connect(('localhost',8000))
		self.wsin = InThread(self.client)
		self.wsin.setName('In ' + str(number))
		self.wsin.start()
		self.wsout = OutThread(self.client)
		self.wsout.setName('Out ' + str(number))
		self.wsout.start()
		self.connected = True
		
		# handshake
		handshake = ['Upgrade: websocket','Connection: Upgrade','Host: localhost:8000','Origin: http://localhost','Sec-WebSocket-Key: FuFD8oZG29J+f0NI4qds/g==','Sec-WebSocket-Version: 13']
		self.client.send("\r\n".join(handshake) + "\r\n")

		# register
		self.wsout.send({'cmd':'reg','reg':self.randStr(rand(10,15))})

		# get user list
		self.wsout.send({'cmd':'list'})
		self.registered = True
		threading.Thread.__init__ ( self )
		
	def randStr(self, len):
		rzygi = ''
		for i in range(len):
			rzygi += chr(rand(97,122))
		return rzygi

	def run(self):
		self.running = True
		while self.running:
			#try:
			self.wsout.send({'cmd':'msg','msg':self.randStr(rand(0,50))})
			sleep(0.5)
		
		# disconnect
		self.wsin.running = False
		self.wsout.running = False
		self.client.shutdown(socket.SHUT_RDWR)
		self.client.close()
		self.connected = False

CLIENTS = int(''.join(sys.argv[1:]))
print 'Launching', CLIENTS, 'clients...'
clients = []
for i in range(1,CLIENTS+1):
	c = DummyClient(i)
	c.daemon = True
	c.setName('Client ' + str(i))
	while not c.registered:
		pass
	c.start()
	clients.append(c)
print 'Running'
run = True
while run:
	try:
		pass
	except KeyboardInterrupt:
		print 'Stopping clients...'
		for i in range(1,CLIENTS+1):
			c = clients.pop()
			c.running = False
			while c.connected:
				pass
		run = False
print 'Finished'