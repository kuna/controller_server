from serverTCP import *

cs = ConnServer()
cs.daemon = True

#ss = SendServer()
#ss.initSock()

gs = GameServer()
gs.daemon = True

#cs.setSendServer(ss)
gs.start()
cs.start()
#cs.startServer()

# start recv input
while 1:
	try:
		input = raw_input()
		if input=="q":
			cs.release()
			break;
		else:
			cs.executeCommand(input)
	except KeyboardInterrupt:
		cs.release()
		break;

print "Bye!"
exit()
