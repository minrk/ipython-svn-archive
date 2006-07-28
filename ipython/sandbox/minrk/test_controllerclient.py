
import cPickle as pickle
import sys
from optparse import OptionParser

from random import randint
from ipython1.kernel.controllerclient import RemoteController
        
    
def main(port, host):
    rc = RemoteController((host, port))
    id =  rc.status().keys()
    print rc.status()
    rc['a'] = 5
    rc.push('a', 6, id[3])
    rc.push('b', 4, id[2:4])
    rc.execute('a*b', id[:6], block=True)
    print rc.status()
    
    


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
