from struct import unpack
from time import time
#TODO LIMITATION: non-fin, continuation/binary

class WebSocketFrame:
	# convert positive integer into binary represented as boolean array (left-filled with False up to a full byte)
	def getBits(self, decval):
		rzygi = []
		while decval > 0:
			rzygi.append(decval % 2 == 1)
			decval = decval >> 1
		if (len(rzygi) % 8) > 0:
			rzygi.extend([False] * (8 - (len(rzygi) % 8)))
		rzygi.reverse()
		return rzygi
	
	# convert a boolean array into a hex value
	def getHex(self, bitArray):
		rzygi = 0
		bitArray.reverse()
		for i in range(len(bitArray)):
			rzygi = rzygi + bitArray[i] * 2**i
		return hex(rzygi)

class WebSocketOutput(WebSocketFrame):
	# init response frame
	def __init__(self, message, key = False):
		self.msg = []
		for i in range(len(message)):
			self.msg.append(hex(ord(message[i])))
		self.maskHex = key
	
	# encode response frame
	def encode(self):
		# control fields (1 byte)
		self.data = ['0x81'] # 0x81 = 1(fin)000(ext)0001(text)
		
		# is_masked, content length (1-9 bytes)
		self.payload_length = len(self.msg)
		payloadLenExtended = []
		# size A: 0-125 (7 bits)
		if self.payload_length < 126:
			payload_size = self.payload_length
		# size B: 16bit uint (2 bytes)
		# TODO: the following two blocks may be merged into one else
		elif self.payload_length < 65536:
			payload_size = 126
			tmp = self.getBits(self.payload_length)
			for i in range(len(tmp)/8):
				payloadLenExtended.append(self.getHex(tmp[i*8:(i+1)*8]))
			if len(payloadLenExtended) == 1:
				payloadLenExtended.insert(0, hex(0))
		# size C: 64bit uint (8 bytes)
		else:
			payload_size = 127
			tmp = self.getBits(self.payload_length)
			for i in range(len(tmp)/8):
				payloadLenExtended.append(self.getHex(tmp[i*8:(i+1)*8]))
			if len(payloadLenExtended) < 8:
				for i in range(8 - len(payloadLenExtended)):
					payloadLenExtended.insert(0, hex(0))
			
		tmp = self.getBits(payload_size)
		tmp[0] = bool(self.maskHex)
		self.data.append(self.getHex(tmp))
		self.data.extend(payloadLenExtended)
		
		# masking key (0-4 bytes)
		if self.maskHex:
			self.data.extend(self.maskHex)
		
		# remaining bytes, payload data
		self.payload = []
		if self.maskHex:
			for i in range(self.payload_length):
				masking_byte = int(self.maskHex[i%4],16)
				masked = int(self.msg[i],16)
				self.payload.append( hex(masked ^ masking_byte) )
		else:
			for i in range(self.payload_length):
				self.payload.append( self.msg[i] )
		self.data.extend(self.payload)
		
		# glue the frame together
		frame = ''
		for i in range(len(self.data)):
			frame += chr(int(self.data[i],16))
		return frame


class WebSocketInput(WebSocketFrame):
	# parse the frame
	def __init__(self, frame):
		self.frame_length = len(frame)
		self.data = unpack(str(self.frame_length) + 'B', frame)
		
		# control fields (1 byte)
		tmp = self.getBits(self.data[0])
		self.fin = tmp[0]
		self.resv1 = tmp[1]
		self.resv2 = tmp[2]
		self.resv3 = tmp[3]
		opcode = self.getHex(tmp[4:8])
		if opcode == '0x0':
			self.opcode = 'continuation'
		elif opcode == '0x1':
			self.opcode = 'text'
		elif opcode == '0x2':
			self.opcode = 'binary'
		elif opcode > '0x2' and opcode < '0x8':
			self.opcode = 'reserved'
		elif opcode == '0x8':
			self.opcode = 'close'
		elif opcode == '0x9':
			self.opcode = 'ping'
		elif opcode == '0xa':
			self.opcode = 'pong'
		else:
			self.opcode = 'invalid'
		offset = 2 # for both control fields, is_masked and payload_size
		
		if self.opcode == 'close':
			return
		
		# is_masked, content length (1-9 bytes)
		tmp = self.getBits(self.data[1])
		self.masked = tmp[0]
		payload_size = int(self.getHex(tmp[1:8]), 16)
		# size A: 0-125 (7 bits)
		if payload_size < 126:
			self.payload_length = payload_size
		# size B: 16bit uint (2 bytes)
		# TODO: the following two elifs may be merged into one else with offset=len(tmp)
		elif payload_size == 126:
			tmp = map(self.getBits, self.data[2:4])
			self.payload_length = []
			for i in range(len(tmp)):
				self.payload_length.extend(tmp[i])
			self.payload_length = int(self.getHex(self.payload_length),16)
			offset += 2
		# size C: 64bit uint (8 bytes)
		elif payload_size == 127:
			tmp = map(self.getBits, self.data[2:10])
			self.payload_length = []
			for i in range(len(tmp)):
				self.payload_length.extend(tmp[i])
			self.payload_length = int(self.getHex(self.payload_length),16)
			offset += 8
		# invalid size
		else:
			pass
		
		# byte 3-6, masking key (optional)
		if self.masked:
			self.mask = []
			self.maskHex = []
			for i in range(4):
				self.mask.append(self.getBits(self.data[i + offset]))
				self.maskHex.append(self.getHex(self.mask[i]))
			offset += 4
		
		# remaining bytes, payload data
		self.payload = ''
		for i in range(self.payload_length):
			#content_byte = int(self.getHex(self.getBits(self.data[i + offset])),16)
			content_byte = self.data[i + offset]
			if self.masked:
				self.payload += chr(content_byte ^ int(self.maskHex[i%4],16))
			else:
				self.payload += chr(content_byte)


def WebSocketPing(key, timestamp=False):
	data = ['0x89','0x8a'] # 0x89 = fin,ping 0x8a = masked,len=10
	data.extend(key)
	if timestamp:
		t = str(timestamp)
	else:
		t = str(int(time()))
	for i in range(10):
		masking_byte = int(key[i%4],16)
		masked = ord(t[i])
		data.append(hex(masked ^ masking_byte))
	frame = ''
	for i in range(len(data)):
		frame += chr(int(data[i],16))
	return frame

def WebSocketPong(key, timestamp=False):
	data = ['0x8a','0x8a'] # 0x8a = fin,pang 0x8a = masked,len=10
	data.extend(key)
	if timestamp:
		t = str(timestamp)
	else:
		t = str(int(time()))
	for i in range(10):
		masking_byte = int(key[i%4],16)
		masked = ord(t[i])
		data.append(hex(masked ^ masking_byte))
	frame = ''
	for i in range(len(data)):
		frame += chr(int(data[i],16))
	return frame

# import pdb;
# pdb.set_trace()
# ping = WebSocketPing(['0x89','0x21','0xa7','0x4b'])
# input = '\x81\x82\x89\x2a\xa7\x4b\xe1\x43' # hi
# test = WebSocketInput(input)
# back = WebSocketOutput(test.payload, test.maskHex)
# back = WebSocketOutput(str(5), ['0x89','0x21','0xa7','0x4b'])
# output = back.encode()
# pass