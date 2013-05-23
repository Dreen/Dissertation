from hashlib import sha1
from base64 import b64encode
from SocketServer import BaseRequestHandler

from WSFrame import WebSocketInput

import pdb

MAGIC = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
HANDSHAKE = [
'HTTP/1.1 101 Web Socket Protocol Handshake', # HTTP/1.1 101 Switching Protocols
'Upgrade: websocket',
'Connection: Upgrade',
'Sec-WebSocket-Accept: ' ]

class WSConnectionHandler(BaseRequestHandler):
	
	# message inbound
	def handle(self):
		self.handshaken = False
		self.server_running = True
		while self.server_running:
			# LIMITATION: data > 1024 bytes
			self.data = self.request.recv(1024).strip()
			
			# its a handshake
			if not self.handshaken:
				self.headers = self.headsToDict(self.data.split("\n"))
				self.key = self.headers["Sec-WebSocket-Key"]
				accept = b64encode(sha1(self.key + MAGIC).hexdigest().decode('hex'))
				response = ''
				for i in range(len(HANDSHAKE)):
					row = HANDSHAKE[i]
					if i == len(HANDSHAKE) - 1:
						if self.c.out: # TEMP FIX TODO output isnt open yet, use a buffer which is then loaded after registering
							self.c.log('< ' + row + accept)
						response += row + accept + "\r\n\r\n"
					else:
						if self.c.out: # TEMP FIX TODO output isnt open yet, use a buffer which is then loaded after registering
							self.c.log('< ' + row)
						response += row + "\r\n"
				self.request.send(response)
				self.handshaken = True
			# its a normal message
			else:
				try:
					try:
						frame = WebSocketInput(self.data)
					except IndexError:
						self.request.close()
						self.server_running = False
				
					if frame.opcode == 'close':
						self.request.close()
						self.server_running = False
					else:
						self.handleMsg(frame)
				except UnboundLocalError: # TODO
					#pdb.set_trace() see unbounderror_info.txt
					pass
	
	# convert HTTP headers in a message to a handy dictionary
	def headsToDict(self, hdata):
		rzygi = {}
		for item in hdata:
			item = item.split(':')
			if len(item) > 1:
				if self.c.out: # TEMP FIX TODO output isnt open yet, use a buffer which is then loaded after registering
					self.c.log('> ' + ':'.join(item))
				rzygi[item[0].strip()] = item[1].strip()
		return rzygi