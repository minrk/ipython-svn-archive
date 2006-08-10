"""A test script for the methods of kernel.controllerclient.RemoteController
It expects a Controller to be running, the default location for the script
to look for the controller is at 127.0.0.1:10105.

methods to test:

execute
push
pull
status
getResult
reset

other aspects to test:
EngineProxy/Subcluster dictionary access to RemoteController

"""
import cPickle as pickle
import sys
from optparse import OptionParser

from random import randint
from ipython1.kernel.controllerclient import RemoteController
        
    
def main(port, host):
    rc = RemoteController((host, port))
    id =  rc.statusAll().keys()
    
    print "Running on %i engines" %len(id)
    if not id:
        print "need some engines!"
        return
    
    print "Testing Push"
    print rc.push(0, a=5)
    print rc.push([0], b='asdf')
    print rc.push([0,1], c=[1,2,3])
    print rc.push('all', a=1, b=2, c=3)
    print rc.push(id, q={'a':5})
    rc['z'] = 'test'
    rc[1]['t'] = [1,2,3]
    rc[0:5]['r'] = 'asdf'
    rc[0:4:2]['asdf'] = 4
    rc[1:4][1]['qwert'] = 3
    
    


def start(port=10105, host='127.0.0.1'):
    parser = OptionParser()
    parser.set_defaults(port=port)
    parser.set_defaults(host=host)
    parser.add_option("-p", "--port", type="int", dest="port",
        help="the TCP port the controller listens on")
    parser.add_option("-a", "--address", type="str", dest="host",
        help="the ip address of the controller")
    (options, args) = parser.parse_args()
    print "connecting to controller at %s:%i" % (options.host, options.port)
    main(options.port, options.host)

if __name__ == "__main__":
    start()
