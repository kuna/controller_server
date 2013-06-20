from socket import *
from SocketServer import ThreadingTCPServer, StreamRequestHandler
from threading import Thread
import sys, hashlib, base64

from proc2 import ConnProc
import time

handshakekey = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
handshake = "HTTP/1.1 101 Switching Protocols\r\n" + \
"Upgrade: websocket\r\n" + \
"Connection: Upgrade\r\n" + \
"Sec-WebSocket-Accept: %s\r\n" + \
"\r\n"

def getConnType(conn):
	for i in range(len(g_connid)):
		if g_connlist[i] == conn:
			return g_conntype[i]
	return "TCP"    # default is TCP

class RecvServer(StreamRequestHandler):
	def handle(self):
		print 'connectionfrom(TCP)', self.client_address
		conn = self.request

		while 1:
			msg=conn.recv(1024)
			if not msg:
				conn.close()
				print self.client_address, 'disconnected'
				break
			#print self.client_address, msg

			if (msg == 'CONNCON'):
				g_connlist.append(conn)
				g_connid.append(msg)
				g_conntype.append("TCP")
	
			r = g_p.ProcCommand(msg, conn, getConnType(conn))
			if not r:
				pass
			else:
				print( "-> %s"%r )

class WebSocketServer(StreamRequestHandler):
	def parse_headers(self, data):
		headers = {}
		lines = data.splitlines()
		for l in lines:
			parts = l.split(": ", 1)
			if len(parts) == 2:
				headers[parts[0]] = parts[1]
		headers['code'] = lines[len(lines) - 1]
		return headers

	def handle(self):
		print 'connection from(WS)', self.client_address
		conn = self.request

		# do handshake first
		data = conn.recv(2048)
		headers = self.parse_headers(data)

		key = headers['Sec-WebSocket-Key']
		resp_data = handshake %((base64.b64encode(hashlib.sha1(key+handshakekey).digest()),))
		conn.send(resp_data)
		handshaken = True
		print "HANDSHAKED ", self.client_address

		g_connlist.append(conn)
		g_connid.append("")     # msg
		g_conntype.append("WS")
		
		while 1:
			_data = conn.recv(128)
			if (not _data):
				print 'sock disconnect', self.client_address
				break  # invalid socket connection
			data = bytearray(_data)
			assert(0x1 == (0xFF & data[0]) >> 7)    # fin bit must be set
			assert(0x1 == (0xFF & data[1]) >> 7)    # data is masked
			if not (0x1 == (0xF & data[0])):        # 0x8 data is close signal
				print 'sock disconnection (by client)', self.client_address
				break

			datalen = (0x7F & data[1])

			str_data = ''
			if (datalen > 0):
				mask_key = data[2:6]
				masked_data = data[6:(6+datalen)]
				unmasked_data = [masked_data[i]^mask_key[i%4] for i in range(len(masked_data))]
				str_data = str(bytearray(unmasked_data))

				r = g_p.ProcCommand(str_data, conn, getConnType(conn))
				if not r:
					pass
				else:
					print( "-> %s"%r )

class ConnWebServer(Thread):
	def __init__(self):
		Thread.__init__(self)
		self.WSPORT = 1240
		self.init = False
		self.startrecv = False
		
		global g_p
		g_p = ConnProc()

		global g_connlist
		g_connlist = []
		global g_connid
		g_connid = []
		global g_conntype
		g_conntype = []

	def run(self):
		self.initSock()

	def executeCommand(self, cmd):
		# not implemented yet
		#print 
		r = g_p.ProcCommand(cmd)
		print r

	def initSock(self):

		try:
			self.clientWS = ThreadingTCPServer( ('', self.WSPORT), WebSocketServer, False)
			print 'listening on PORT(WS)', self.WSPORT
			self.clientWS.allow_reuse_address = True
			self.clientWS.server_bind()
			self.clientWS.server_activate()
			self.clientWS.serve_forever()
		except Exception, e:
			print e

		self.init = True;
	def release(self):
		if (not self.init):
			return

		self.startrecv = False
		self.clientWS.shutdown()
		self.init = False

	def printLog(self, msg):
		print msg




class ConnServer(Thread):
	def __init__(self):
		Thread.__init__(self)
		self.PORT = 1236
		self.init = False
		self.startrecv = False
		
		global g_p
		g_p = ConnProc()

		global g_connlist
		g_connlist = []
		global g_connid
		g_connid = []

	def run(self):
		self.initSock()

	def executeCommand(self, cmd):
		# not implemented yet
		#print 
		r = g_p.ProcCommand(cmd)
		print r

	def initSock(self):

		try:
			self.client = ThreadingTCPServer( ('', self.PORT), RecvServer, False)
			print 'listening on PORT(TCP)', self.PORT
			self.client.allow_reuse_address = True
			self.client.server_bind()
			self.client.server_activate()
			self.client.serve_forever()
		except Exception, e:
			print e

		self.init = True;
	def release(self):
		if (not self.init):
			return

		self.startrecv = False
		self.client.shutdown()
		self.init = False

	def printLog(self, msg):
		print msg


class GameServer(Thread):
	def __init__(self):
		Thread.__init__(self)
		self.SERVERPORT = 1235
		self.init = False

	def run(self):
		while (True):
			try:
				if (self.initSock()):
					self.recv()
			except Exception, e:
				print e
				print 'recreate server socket after 5 sec...'
				time.sleep(5)
				continue
			print 'recreate server socket after 5 sec...'
			time.sleep(5)

	def initSock(self):
		try:
			self.server = socket(AF_INET, SOCK_STREAM)
			self.server.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
			self.server.bind( ('', self.SERVERPORT) )
			self.server.listen(5)
			
			print 'SERVER CONNECTED'
		except Exception, e:
			print 'SERVER CONNECTION FAILED'
			print e
			return False

		self.init = True
		return True
	def recv(self):
		
		while self.init:
			conn, addr = self.server.accept()
			self.sc = conn
			print '[Game] conncection from', addr
			g_p.SetServerConn(self)
			while True:
				data = conn.recv(1024)
				if not data:
					conn.close()
					print 'connection disconnected'
					self.init = False
					break
				if (data == 'CLOSE'):
					conn.close()
					print 'game closed'
					self.init = False
					break
		
				print 'recv cmd: %s' % data
				r = g_p.ProcCommand(data, conn, "TCP")
		
				# is this command is returned to server
				# or notified to clients?
		
				if not r:
					pass
				else:
					print( "-> %s" % r )

	def sendEncode(self, data):
		if not self.sc:
			pass
		else:
			self.sc.send( data.encode('utf-8') )

	def release(self):
		if (not self.init):
			return
		
		self.server.close()
		self.init = False
