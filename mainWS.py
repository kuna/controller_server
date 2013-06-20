from serverWS import *

cs = ConnServer()
cs.daemon = True

cws = ConnWebServer()
cws.daemon = True

#ss = SendServer()
#ss.initSock()

gs = GameServer()
gs.daemon = True

#cs.setSendServer(ss)
gs.start()
cs.start()
cws.start()
#cs.startServer()

# start recv input
while 1:
	try:
		input = raw_input()
		if input=="q":
			if (cs is not None):
				cs.release()
			if (cws is not None):
				cws.release()
			gs.release()
			break;
		else:
			cs.executeCommand(input)
	except KeyboardInterrupt:
                if (cs is not None):
			cs.release()
                if (cws is not None):
			cws.release()
                gs.release()
		break;

print "Bye!"
exit()
