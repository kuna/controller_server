GAME_NONE = 0
GAME_ROOM = 1
GAME_PLAY = 2
GAME_RESULT = 3

class ConnProc:
	def __init__(self):
		self.roomcnt = 0
		self.conncnt = 0
		self.connid = []
		self.connlist = {}
		self.state = GAME_NONE
	
	def SetServerConn(self, conn):
		self.sc = conn

	def Encode(self, data):
		return data.encode('utf-8')

	def ProcCommand(self, msg, conn):
		data = msg.split("\n")
		for x in data
			self._ProcCommand(x.strip(), conn)

	def _ProcCommand(self, msg, conn):
		args = msg.split(" ")

		# ############## #
		# Server Side ## #
		# ############## #

		# game part
		if (args[0] == "CONN"):
			self.conncnt = 0
			self.roomcnt = 0
			self.connid = []
			self.connlist = {}
			self.state = GAME_NONE
			return "OK CONN"

		if (args[0] == "ROOM"):
			self.roomcnt = int(args[1])
			print "room max: %d" % self.roomcnt
			self.state = GAME_ROOM
			for i in range(self.roomcnt):
				self.connid.append( [args[i+2], None] )
				print "room: %s" % args[i+2]


		# ############## #
		# Client Side ## #
		# ############## #

		#client(conn) part
		if (args[0] == "JOIN"):
			if (self.state != GAME_ROOM):
				return "ERROR"

			# search for valid device code
			isConnfound = False
			for i in range(self.roomcnt):
				if self.connid[i][0]==args[1]:
					self.connid[i][1] = conn
					isConnfound = True
					print "Joined id: %s" % self.connid[i][0]
					break

			if not isConnfound:
				print "Invalid connection id: %s" % args[1], self.connid[0][0]
				return "ERROR JOIN"
			
			self.conncnt += 1
			if (self.conncnt == self.roomcnt):
				self.sc.sendEncode( "OK JOIN ALL" )
				for i in range(self.roomcnt):
					self.connid[i][1].send(self.Encode("OK JOIN ALL"))
			else:
				self.sc.sendEncode( "OK JOIN %s" % args[1] )
				return "OK JOIN %s" % args[1]
			

		if (args[0] == "STARTGAME"):
			self.state = GAME_PLAY
			


		if (args[0] == "PING"):
			return "PONG %s"%args[1]

		if (args[0] == "QUIT"):
			# check is logined
			for i in range(self.roomcnt):
				self.connid[i][1].send( self.Encode("QUIT") )
				self.connid[i][1].close()
			self.sc.sendEncode("QUIT")
			self.sc.release()
			return "QUIT BY SERVER"
			
		if (args[0] == "MODIFY"):
			if (self.state != GAME_PLAY):
				return "ERROR"

			for i in range(self.roomcnt):
				if (args[1] == "ALL"):
					self.connid[i][1].send( self.Encode(msg) )
					continue

				if (self.connid[i][0] == args[1]):
					# send data after modification
					#data = msg.replace("EVENT", "MODIFY", 1)
					self.connid[i][1].send( self.Encode(msg) )
					break

		if (args[0] == "EVENT"):
			self.sc.sendEncode(msg)
