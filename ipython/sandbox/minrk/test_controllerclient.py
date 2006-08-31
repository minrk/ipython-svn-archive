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
import sys, StringIO
from optparse import OptionParser

from random import randint
from ipython1.kernel.api import RemoteController
        

def main(port, host):
    rc = RemoteController((host, port))
    ids = rc.getIDs()
    hide = StringIO.StringIO('')    
    print "Running on %i engines" %len(ids)
    if not ids:
        print "need some engines!"
        return
    
    print "Testing push/pull"
    try:
        assert rc.push(0, a=5),"assert rc.push(0, a=5)"
        assert rc.pull(0, 'a') == 5,"assert rc.pull(0, 'a') == 5"
        assert not rc.push(0),"assert not rc.push(0)"
        assert not rc.push([], a=5),"assert not rc.push([], a=5)"
        assert rc.push([0], b='asdf', c=[1,2]),"assert rc.push([0], b='asdf', c=[1,2])"
        assert rc.pull([0], 'b', 'c') == ['asdf', [1,2]],"assert rc.pull([0], 'b', 'c') == ['asdf', [1,2]]"
        assert rc.pushAll(c=[1,2,3]),"assert rc.pushAll(c=[1,2,3])"
        assert rc.pullAll('c') == ([1,2,3],)*len(ids),"assert rc.pullAll('c') == ([1,2,3],)*len(ids)"
        assert rc.push([0,0], a=14),"assert rc.push([0,0], a=14)"
        assert rc.pull([0,0,0], 'a') == (14,14,14),"assert rc.pull([0,0,0], 'a') == (14,14,14)"
        assert rc.pushAll(a=1, b=2, c=3),"assert rc.pushAll(a=1, b=2, c=3)"
        assert rc.pullAll('a','b','c') == [(1,)*len(ids),(2,)*len(ids),(3,)*len(ids)],"assert rc.pullAll('a','b','c') == [(1,1)*len(ids),(2,2)*len(ids),(3,3)*len(ids)]"
        q={'a':5}
        assert rc.push(ids, q=q),"assert rc.push(ids, q=q)"
        assert rc.pull(ids,'q') == (q,)*len(ids) or len(ids) is 1,"assert rc.pull(ids,'q') == (q,)*len(ids)"
        rc['z'] = 'test'
        rc[1]['t'] = [1,2,3]
        rc[0:max(ids)]['r'] = 'asdf'
        rc[0:max(ids):2]['asdf'] = 4
        rc[1:max(ids)][1]['qwert'] = 3
    except Exception, e:
       print "push/pull FAIL: ", e
    else:
       print "push/pull OK"
    
    print "Testing push/pullNamespace"
    try:
        ns = {'a':5}
        assert rc.pushAll(**ns),"assert rc.pushAll(a=5)"
        assert rc.pullNamespace(0, 'a') == ns,"assert rc.pullNamespace(0, 'a') == {'a':5}"
        assert rc.pullNamespaceAll('a') == [ns]*len(ids),"assert rc.pullNamespaceAll('a') == [{'a':5}]*len(ids)"
        ns['b'] = 6
        ns['cd'] = 'asdf'
        assert rc.pushAll(**ns),"assert rc.pushAll(a=5, b=6, cd='asdf')"
        assert rc.pullNamespace(0, *ns.keys()) == ns,"assert rc.pullNamespace(0, *ns.keys()) == ns"
        assert rc.pullNamespaceAll(*ns.keys()) == [ns]*len(ids),"assert rc.pullNamespaceAll(*ns.keys) == [ns]*len(ids)"
    except Exception, e:
        print "pushAll/pullNamespace FAIL: ", e
    else:
        print "pushAll/pullNamespace OK"
        
    print "Testing execute"
    try:
        assert rc.execute(0, 'a'),"assert rc.execute(0, 'a')"
        assert rc.executeAll('print a'),"assert rc.execute([0,1], 'print a')"
        assert rc.execute('all', 'b-3'),"assert rc.execute('all', 'b-3')"
        assert not rc.execute(0, ''),"assert not rc.execute(0, '')"
        assert not rc.execute([], 'locals'),"assert not rc.execute([], 'locals')"
        s = sys.stdout
        sys.stdout = hide
        assert rc.execute(0, 'a', block=True),"assert rc.execute(0, 'a', block=True)"
        assert rc.execute([0,0], 'print a', block=True),"assert rc.execute([0,1], 'print a', block=True)"
        assert rc.execute('all', 'b-3', block=True),"assert rc.execute('all', 'b-3', block=True)"
        assert not rc.execute(0, '', block=True),"assert not rc.execute(0, '', block=True)"
        assert not rc.execute([], 'locals', block=True),"assert not rc.execute([], 'locals', block=True)"
        sys.stdout = s
    except Exception, e:
        print "execute FAIL: ", e
    else:
        print "execute OK"
    
    # print "Testing status/reset"
    # try:
    #     pass
    # except Exception, e:
    #     print 'status/reset FAIL: ', e
    # else:
    #     print 'status/reset OK'



    # print "Testing "
    # try:
    #     pass
    # except Exception, e:
    #     print 'test FAIL: ', e
    # else:
    #     print 'test OK'
    


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
