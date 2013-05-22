from socket import *
from threading import Thread

from proc import ConnProc

class ConnServer(Thread):
	def __init__(self):
		Thread.__init__(self)
		self.PORT = 1234
		self.init = False
		self.startrecv = False
		self.p = ConnProc()

	def setSendServer(self, _ss):
		self.ss = _ss

	def run(self):
		self.startServer()

	def executeCommand(self, cmd):
		# not implemented yet
		#print "you entered - ", cmd
		r = self.p.ProcCommand(cmd)
		print r

	def startServer(self):
		if (self.initSock()):
			self.startRecv()
			
	def initSock(self):
		try:
			if (self.init):
				return False

			self.sock = socket(AF_INET, SOCK_DGRAM)
			#self.sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1) #reuse TIME_WAIT state
			self.sock.bind( ('', self.PORT) )
			self.init = True			
		except Exception, e:
			print "unknown error occured - ", e
			return False

		print("* Server start!")
		return True
	def startRecv(self):
		self.startrecv = True
		while (self.startrecv):
			msg, addr = self.sock.recvfrom(1024)
			
			r = self.p.ProcCommand(msg)
			if (r != None and self.ss != None):
				#self.ss.sendData(addr[0], r) 
				self.ss.sendDataAddr(addr, r)			

			# for debugging
			print msg, addr, r
			

	def release(self):
		if (not self.init):
			return

		self.startrecv = False
		self.sock.close()
		self.init = False		

	def printLog(self, msg):
		print msg

class SendServer:
	def __init__(self):
		self.PORT = 1235
		self.init = False

#	def startServer(self):
#		return self.initSock()

	def initSock(self):
		try:
			if (self.init):
				return False

			self.sock = socket(AF_INET, SOCK_DGRAM)
			self.init = True
		except Exception, e:
			print "unknown error occured - ", e
			return False

		print "* Send Server start!"
		return True

	def release(self):
		if (not self.init):
			return

		self.sock.close()
		self.init = False

	def sendData(self, ip, obj):
		if (not self.init):
			return False
		
		s = unicode(obj)
		self.sock.sendto(s, (ip, self.PORT))
		return True

	def sendDataAddr(self, addr, obj):
		if (not self.init):
			return False

		s = unicode(obj)
		self.sock.sendto(s, addr)
		return True
