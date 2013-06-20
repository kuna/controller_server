import random

GAME_NONE = 0
GAME_ROOM = 1
GAME_PLAY = 2
GAME_RESULT = 3

GAME_SELECT = 10

# SUPPORT WebSocket & Socket!!

class ConnProc:
	def __init__(self):
		self.roomcnt = 0
		self.conncnt = 0
		self.connid = []
		self.conntype = []
		self.state = GAME_NONE

		# ############# #
		# for character #
		# ############# #
		self.charsel = []
	
	def SetServerConn(self, conn):
		self.sc = conn

	def Encode(self, data, ptype):
                if (ptype == "WS"):
                        # 1st byte: fin bit set
                        # 2nd byte: length set in 1 byte
                        resp = bytearray([0b10000001, len(data)])

                        for d in bytearray(data):
                            resp.append(d)
                        return resp
                elif (ptype == "TCP"):
                        return data.encode('utf-8')

	def GetType(self, id):
		for i in range(self.roomcnt):
			if (id == self.connid[i][0]):
				return self.conntype[i]
		return "TCP"

	def ProcCommand(self, msg, conn, ptype):
		data = msg.split("\n")
		
		for x in data:
			try:
                                r = self._ProcCommand(x.strip(), conn, ptype);
                                if (r is not None):
                                        print r
			except Exception, e:
				print e
				print "[ERROR MSG] %s"%x

	def _ProcCommand(self, msg, conn, ptype):
		args = msg.split(" ")

		# ############## #
		# Server Side ## #
		# ############## #

		# game part
		if (args[0] == "CONN"):
			self.conncnt = 0
			self.roomcnt = 0
			self.connid = []
			self.conntype = []
			self.state = GAME_NONE

			self.charsel = []
			
			self.sc.sendEncode("OK CONN\n")

		if (args[0] == "ROOM"):			
			self.roomcnt = int(args[1])
                        retstr = "ROOM %d" % self.roomcnt

			print "room max: %d" % self.roomcnt

			self.state = GAME_ROOM
			for i in range(self.roomcnt):
	                        # create room code
        	                _rn = random.randint(0, 9999)
                	        _rstr = "%04d"%_rn
				self.connid.append( [_rstr, None] )
				self.charsel.append( 0 )
				self.conntype.append( "TCP" )
				print "room: %s" % _rstr

				retstr = "%s %s" % (retstr, _rstr)

			# return random created codes
			retstr = "%s\n" % retstr
			self.sc.sendEncode(retstr)
			

		# ############## #
		# Client Side ## #
		# ############## #

		#client(conn) part
		if (args[0] == "JOIN"):
			if (self.state != GAME_ROOM):
				conn.send( self.Encode("ERROR NOROOM\n", ptype) )
				return "ERROR JOIN - no room"

			# search for valid device code
			isConnfound = False
			for i in range(self.roomcnt):
				if self.connid[i][0]==args[1]:
					self.connid[i][1] = conn
					self.conntype[i] = ptype
					isConnfound = True
					print "Joined id: %s" % self.connid[i][0]
					break

			if not isConnfound:
				print "Invalid connection id: %s" % args[1], self.connid[0][0]
				conn.send( self.Encode( "ERROR JOINCODE\n", ptype))
				return "ERROR JOINCODE"

                        self.sc.sendEncode( "OK JOIN %s\n" % args[1] )
                        conn.send( self.Encode( "OK JOIN %s\n"%args[1], ptype ))

			self.conncnt += 1
			if (self.conncnt == self.roomcnt):
				self.sc.sendEncode( "OK JOIN ALL\n" )
				for i in range(self.roomcnt):
					self.connid[i][1].send(self.Encode("OK JOIN ALL\n", ptype))
					#self.connid[i][1].send(self.Encode("MODIFY ALL gogun ui\n"))
		
				# ################# #
				# go to select mode #
				# ################# #
				
				self.state = GAME_SELECT
				for i in range(self.roomcnt):
					self.connid[i][1].send(self.Encode("MODIFY ALL Flag select\n", ptype))
				return "OK JOIN ALL"


			return "OK JOIN %s" % args[1]
			

		if (args[0] == "ENDGAME"):
			self.state = GAME_RESULT

		if (args[0] == "RESULT"):	# RESULT (id) (score) (win?0:1)
			for i in range(self.roomcnt):
				if (self.connid[i][0] == args[1]):
                                        # 0. record score of user (not implemented)

					_ptype = self.GetType(self.connid[i][0])

					# 1. change screen to User
					if (int(args[3])==1):
						self.connid[i][1].send( self.Encode( "MODIFY ALL Flag win\n", _ptype ))
					else:
                                                self.connid[i][1].send( self.Encode( "MODIFY ALL Flag lose\n", _ptype))

					# 2. change id to score
					self.connid[i][1].send(self.Encode("EDIT ALL 100 button text %d\n"%1234, _ptype))	# score
					break

		if (args[0] == "PING"):
			conn.send(self.Encode("PONG %s\n"%args[1], ptype))

		if (args[0] == "MODIFY"):
			if (self.state != GAME_PLAY):
				conn.send( self.Encode("ERROR\n", ptype))

			for i in range(self.roomcnt):
				if (args[1] == "ALL"):
					self.connid[i][1].send( self.Encode("%s\n"%msg, self.conntype[i] ) )
					continue

				if (self.connid[i][0] == args[1]):
					# send data after modification
					#data = msg.replace("EVENT", "MODIFY", 1)
					self.connid[i][1].send( self.Encode("%s\n"%msg, self.conntype[i] ) )
					break

		if (args[0] == "EVENT"):
			# ############################### #
			# special route for character sel #
			# ############################### #
			if (self.state == GAME_SELECT and int(args[2])==301 ):
				# select character
				if (int(args[3])>1000 and int(args[3])<1010):
					for i in range(self.roomcnt):
						if (self.connid[i][0]==args[1] and self.charsel[i]<10):
							self.charsel[i] = int(args[3])%1000
							self.sc.sendEncode("OK CHARACTER %s %d\n"%(args[1], self.charsel[i]))
							break
		
				# choose character
				if (int(args[3])>=1010):
					for i in range(self.roomcnt):
						if (self.connid[i][0]==args[1] and self.charsel[i]>0):
							self.charsel[i] += 10
                                                        self.sc.sendEncode("OK CHARACTER %s %s\n"%(args[1], self.charsel[i]))
							break

				# if all character is choosed
				charsel = True
				for i in range(self.roomcnt):
					if (self.charsel[i]<10):
						charsel = False
				if(charsel):
					self.sc.sendEncode("OK CHARACTER ALL\n")
					for i in range(self.roomcnt):
						self.connid[i][1].send(self.Encode("MODIFY ALL Flag game\n", self.conntype[i] ))
                                                #self.connid[i][1].send(self.Encode("MODIFY ALL Flag game\n"))


			# ############################## #
			# special route for motion recog #
			# ############################## #
		
			if (len(args) < 3):
				return			

			if (int(args[2])==201):
				vals = args[3].split(",")
				mAngleX = float(vals[0])
				mAngleY = float(vals[1])
				mAngleZ = float(vals[2])
				if (mAngleY < -30):
					self.sc.sendEncode("EVENT %s 400\n"%args[1])	# up: acclY < 10 and acclZ < 9.8-2
				if (mAngleY > 30):
					self.sc.sendEncode("EVENT %s 401\n"%args[1])	# down: acclY > 10 and acclZ > 9.8+2

			if (int(args[2])==200 or int(args[2])==201):
				return

			# ############################# #
			# special route for game replay #
			# ############################# #
			if (self.state == GAME_RESULT and int(args[2]) == 301):
				if (int(args[3]) == 1010): # quit button	
		                        for i in range(self.roomcnt):
                		                self.connid[i][1].send( self.Encode("QUIT\n", self.conntype[i] ) )
		                        self.sc.sendEncode("QUIT\n")
				if (int(args[3]) == 1011): # replay button
					# call replay
					args[0] = "REPLAY"			


			self.sc.sendEncode("%s\n"%msg)


                if (args[0] == "REPLAY"):
                        # call STARTGAME
                        self.sc.sendEncode("REPLAY\n")
                        args[0] = "STARTGAME"

                if (args[0] == "STARTGAME"):
                        self.state = GAME_PLAY
                        for i in range(self.roomcnt):
                                self.connid[i][1].send(self.Encode("MODIFY ALL Flag game\n", self.conntype[i]))


                if (args[0] == "QUIT"):
                        # check is logined
                        for i in range(self.roomcnt):
				if (self.connid[i][1] != None):
                                	self.connid[i][1].send( self.Encode("QUIT\n", self.conntype[i]) )
                                	#self.connid[i][1].close()
                        self.sc.sendEncode("QUIT\n")
                        #self.sc.release()

                        # re-alive to connect another game
                        #self.sc.initSock()
                        return "QUIT BY SERVER"



