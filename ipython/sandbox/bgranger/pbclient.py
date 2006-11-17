from ipython1.kernel.controllerpb import RemoteController
from twisted.internet import reactor

rc = RemoteController(('127.0.0.1', 10111))

def stop(status):
    reactor.stop()

def main(status):
    print "In main with status: ", status
    def printer(o):
        print o
    d = rc.execute('all', 'a = 5')
    d.addCallback(printer)
    d.addCallback(stop)

d1 = rc.connect()
d1.addCallback(main)

reactor.run()
