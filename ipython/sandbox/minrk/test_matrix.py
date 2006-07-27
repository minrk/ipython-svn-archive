
import cPickle as pickle
import sys
from optparse import OptionParser

from random import randint
from ipython1.kernel.controllerclient import RemoteController

class Matrix:
    
    def __init__(self, m=0, n=None):
        if n is None:
            n = m
        self.m = m
        self.n = n
        self.matrix = []
        for a in range(n):
            self.matrix.append([])
            for b in range(n):
                self.matrix[a].append(randint(0,9))
    
    def load(self, matrix):
        self.matrix = matrix
        self.m = len(matrix)
        if self.m:
            self.n = len(matrix[0])
        else:
            self.n = 0
    
    def getCol(self, n):
        return map(list.__getitem__, self.matrix, [n]*self.m)
    
    def getRow(self, m):
        return self.matrix[m]
        
    def __repr__(self):
        s = ''
        for m in range(self.m):
            s += "%s\n" % self.getRow(m)
        return s
    
        
    
def main(port, host):
    rc = RemoteController((host, port))
    n = len(rc.getLastCommandIndex())
    M = Matrix(n)
    print M
    
    for id in range(n):
        rc.push('id', id, id)
    rc.execute("from Numeric import dot")
    rc.execute("from sandbox.test_matrix import Matrix")
    rc.push('m', M.matrix)
    rc.execute('M = Matrix()')
    rc.execute('M.load(m)')
    rc.execute("r = M.getRow(id)")
    rc['v'] = []
    for c in range(n):
        rc.execute("v.append(dot(r,M.getCol(%i)))" %c)
    N = Matrix()
    N.load(rc['v'])
    print N
    


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
