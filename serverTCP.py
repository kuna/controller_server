from socket import *
from SocketServer import ThreadingTCPServer, StreamRequestHandler
from threading import Thread

from proc import ConnProc

class RecvServer(StreamRequestHandler):
	def handle(self):
		print 'connectionfrom', self.client_address
		conn = self.request

		while 1:
			msg=conn.recv(1024)
			if not msg:
				conn.close()
				print self.client_address, 'disconnected'
				break
			print self.client_address, msg

			if (msg == 'CONNCON'):
				g_connlist.append(conn)
				g_connid.append(msg)
	
			r = g_p.ProcCommand(msg, conn)
			if not r:
				pass
			else:
				print( "-> %s"%r )

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
			self.client = ThreadingTCPServer( ('', self.PORT), RecvServer)
			print 'listening on PORT', self.PORT
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
		if (self.initSock()):
			self.recv()

	def initSock(self):
		try:
			self.server = socket(AF_INET, SOCK_STREAM) 
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
		while True:
			conn, addr = self.server.accept()
			self.sc = conn
			print '[Game] conncection from', addr
			g_p.SetServerConn(self)
			while True:
				data = conn.recv(1024)
				if not data:
					conn.close()
					print 'connection disconnected'
					break
				if (data == 'CLOSE'):
					conn.close()
					print 'game closed'
					break
		
				print 'recv cmd: %s' % data
				r = g_p.ProcCommand(data, conn)
		
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
