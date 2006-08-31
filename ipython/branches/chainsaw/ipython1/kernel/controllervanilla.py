
"""The Twisted core of the ipython controller.

This module contains the Twisted protocols, factories, etc. used to
implement the ipython controller.  This module only contains the network related
parts of the controller.
"""

#*****************************************************************************
#       Copyright (C) 2005  Fernando Perez <fperez@colorado.edu>
#                           Brian E Granger <ellisonbg@gmail.com>
#                           Benjamin Ragan-Kelly <<benjaminrk@gmail.com>>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

import socket, cPickle as pickle

from twisted.internet import defer
from twisted.internet.interfaces import IProducer
from twisted.python import components, log
from twisted.python.failure import Failure
from zope.interface import Interface, implements

from IPython.ColorANSI import TermColors

import ipython1.kernel.magic
from ipython1.kernel import controllerservice, serialized, protocols, results
from ipython1.kernel.util import _tar_module
from ipython1.kernel.controllerclient import RCView, EngineProxy

arraytypeList = []
# try:
#    import Numeric
# except ImportError:
#    pass
# else:
#    arraytypeList.append(Numeric.arraytype)
try:
    import numpy
except ImportError:
    pass
else:
    arraytypeList.append(numpy.ndarray)
# try:
#    import numarray
# except ImportError:
#    pass
# else:
#    arraytypeList.append(numarray.numarraycore.NumArray)


arraytypes = tuple(arraytypeList)
del arraytypeList


# The Client Side:
class RemoteController(object):
    """A high level interface to a remotely running ipython controller."""
    
    MAX_LENGTH = 99999999
    
    def __init__(self, addr):
        """Create a RemoteController instance pointed at a specific controller.
        
        @arg addr:
            The (ip,port) tuple of the kernel.  The ip in a string
            and the port is an int.
        """
        self.addr = addr
        self.block = False
        controllerservice.addAllMethods(self)
        self.activate()
    
    def activate(self):
        """Make this cluster the active one for ipython magics.
        
        IPython has a magic syntax to work with InteractiveCluster objects.
        In a given ipython session there is a single active cluster.  While
        there can be many clusters created and used by the user, there is only
        one active one.  The active cluster is used when ever the magic syntax
        is used.  
        
        The activate() method is called on a given cluster to make it the active
        one.  Once this has been done, the magic command can be used:
        
        >>> %px a = 5       # Same as execute('a = 5')
        
        >>> %autopx         # Now every command is sent to execute()
        
        >>> %autopx         # The second time it toggles autoparallel mode off
        """
        try:
            __IPYTHON__.activeController = self
        except NameError:
            print "The IPython Controller magics only work within IPython."
    
    def __del__(self):
        return self.disconnect()
    
    def is_connected(self):
        """Are we connected to the controller?""" 
        if hasattr(self, 's'):
            try:
                self.s.send('')
            except socket.error:
                return False
            else:
                return True
    
    def _check_connection(self):
        """Are we connected to the controller?  If not reconnect."""
        if not self.is_connected():
            return self.connect()
        return True
    
    def connect(self):
        """Initiate a new connection to the controller."""
        
        print "Connecting to controller: ", self.addr
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error, e:
            print "Strange error creating socket: %s" % e
            return False
        try:
            self.s.connect(self.addr)
        except socket.gaierror, e:
            print "Address related error connecting to sever: %s" % e
            return False
        except socket.error, e:
            print "Connection error: %s" % e
            return False
                
        # Turn off Nagle's algorithm to prevent the 200 ms delay :)
        self.s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY,1)
        self.es = protocols.NetstringSocket(self.s)
        self.es.MAX_LENGTH = self.MAX_LENGTH
        return True
    
    def parseTargets(self, targets):
        if isinstance(targets, int):
            if targets >= 0:
                return str(targets)
        elif isinstance(targets, (list, tuple)):
            if not targets:
                return False
            for t in targets:
                if not isinstance(t, int) or t < 0:
                    return False
            return '::'.join(map(str, targets))
        elif targets == 'all':
            return targets
        return False
    
    def multiTargets(self, targets):
        return not isinstance(targets, int) and len(targets) > 1
    
    def executeAll(self, source, block=False):
        return self.execute('all', source, block)
    
    def execute(self, targets, source, block=False):
        """Execute python source code on the ipython kernel.
        
        @arg targets:
            the engine id(s) on which to execute.  targets can be an int, list of
            ints, or the string 'all' to indicate that it should be executed on
            all engines connected to the controller.
        @arg source:
            A string containing valid python code
        @arg block:
            whether or not to wait for the results of the command.
            True:
                wait for results, which will be printed as stdin/out/err
            False:
                do not wait, return as soon as source has been sent, print nothing.
        """
        targetstr = self.parseTargets(targets)
        if not targetstr or not source:
            # need something to do
            return False
        self._check_connection()
        
        if self.block or block:
            string = "EXECUTE BLOCK %s::%s" % (source, targetstr)
            try:
                self.es.writeNetstring(string)
            except socket.error:
                try:
                    self.connect()
                    self.es.writeNetstring(string)
                except socket.error:
                    return False
            string = self.es.readNetstring()
            if string [:3] == 'BAD':
                return False
            data = []
            while string not in ['EXECUTE FAIL', "EXECUTE OK"]:
                package = self.es.readNetstring()
                if string in ["PICKLE RESULT", "PICKLE FAILURE"]:
                    try:
                        data.append(pickle.loads(package))
                    except pickle.PickleError, e:
                        print "Error unpickling object: ", e
                        return False
                else:
                    return False
                string = self.es.readNetstring()
                
            # Now print data
            blue = TermColors.Blue
            normal = TermColors.Normal
            red = TermColors.Red
            green = TermColors.Green
            for cmd in data:
                if isinstance(cmd, Failure):
                    print cmd
                else:
                    target = cmd[0]
                    cmd_num = cmd[1]
                    cmd_stdin = cmd[2]
                    cmd_stdout = cmd[3][:-1]
                    cmd_stderr = cmd[4][:-1]
                    print "%s[%s:%i]%s In [%i]:%s %s" % \
                        (green, self.addr[0], target,
                        blue, cmd_num, normal, cmd_stdin)
                    if cmd_stdout:
                        print "%s[%s:%i]%s Out[%i]:%s %s" % \
                            (green, self.addr[0], target,
                            red, cmd_num, normal, cmd_stdout)
                    if cmd_stderr:
                        print "%s[%s:%i]%s Err[%i]:\n%s %s" % \
                            (green, self.addr[0], target,
                            red, cmd_num, normal, cmd_stderr)
        else:
            string = "EXECUTE %s::%s" % (source, targetstr)
            try:
                self.es.writeNetstring(string)
            except socket.error:
                try:
                    self.connect()
                    self.es.writeNetstring(string)
                except socket.error:
                    return False
            string = self.es.readNetstring()
            data = None
             
        if string == "EXECUTE OK":
            return True
        else:
            return False
    
    def run(self, targets, fname):
        """Run a file on the kernel."""
        
        fileobj = open(fname,'r')
        source = fileobj.read()
        fileobj.close()
        # if the compilation blows, we get a local error right away
        code = compile(source,fname,'exec')
        
        # Now run the code
        return self.execute(targets, source)
    
    def runAll(self, fname):
        return self.run('all', fname)
    
    def sendSerialized(self, serial):
        assert isinstance(serial, serialized.Serialized)
        for line in serial:
            self.es.writeNetstring(line)
    
    def push(self, targets, **namespace):
        """Send python object(s) to the namespace of remote kernel(s).
        
        There is also a dictionary style interface to the push command:
                
        >>> rc = RemoteController(addr)
        
        >>> rc[0]['a'] = 10    # Same as rc.push(0, a=10)
        >>> rc.push([1,2,3], a=5, b=[1], c=c)
            #pushes 5 to a, [1] to b, and the local value c to c on engines [1,2,3]
        
        @arg targets:
            the engine id(s) on which to execute.  targets can be an int, list of
            ints, or the string 'all' to indicate that it should be executed on
            all engines connected to the controller.
        @arg namespace:
            The python objects to send and their remote keys.  i.e. a=1, b='asdf'
        """
        targetstr = self.parseTargets(targets)
        if not targetstr or not namespace or not self._check_connection():
            #need something to do
            return False
        
        string = "PUSH ::%s" % targetstr
        try:
            self.es.writeNetstring(string)
        except socket.error:
            try:
                self.connect()
                self.es.writeNetstring(string)
            except socket.error:
                return False
        
        if self.es.readNetstring() != "PUSH READY":
            return False
        for key in namespace:
            value = namespace[key]
            try:
                serialObject = serialized.serialize(value, key)
            except Exception, e:
                print "Object cannot be serialized: ", key, e
                return False
            else:
                self.sendSerialized(serialObject)
        self.es.writeNetstring("PUSH DONE")
        string = self.es.readNetstring()
        if string == "PUSH OK":
            return True
        elif string == "PUSH FAIL":
            return False
        else:
            return string
    
    def __setitem__(self, key, value):
            return self.push('all', **{key:value})
    
    def pull(self, targets, *keys):
        """Get python object(s) from remote kernel(s).
                
        If the object does not exist in the kernel's namespace a NotDefined
        object will be returned.
        
        Like push, pull also has a dictionary interface:
        
        >>> rc = RemoteController(addr)
        >>> rc[0]['a'] = 10    # Same as rc.push(0, a=10)
        >>> rc[0]['a']         # Same as rc.pull(0,'a')
        10
        
        @arg targets:
            the engine id(s) on which to execute.  targets can be an int, list of
            ints, or the string 'all' to indicate that it should be executed on
            all engines connected to the controller.
        @arg *keys:
            The name of the python objects to get
        
        @returns:
            4 cases:
                1 target, 1 key:
                    the value of key on target
                1 target, >1 keys:
                    a list of the values of keys on target
                >1 targets, 1 key:
                    a tuple of the values at key on targets
                >1 targets, >1 keys:
                    a list of length len(keys) of tuples for each key on targets.
                    equivalent in form to:
                    l = []
                    for t in targets:
                        l.append(rc.pull(t, *keys))
        """
        targetstr = self.parseTargets(targets)
        if not targetstr or not keys or not self._check_connection():
            # need something to do
            return False
        
        try:
            keystr = ','.join(keys)
        except TypeError:
            return False
        
        multitargets = self.multiTargets(targets)
        string = "PULL %s::%s" % (keystr, targetstr)
        try:
            self.es.writeNetstring(string)
        except socket.error:
            try:
                self.connect()
                self.es.writeNetstring(string)
            except socket.error:
                return False
        
        string = self.es.readNetstring()
        if string [:3] == 'BAD':
            return False
        results = []
        returns = []
        while string not in ['PULL OK', 'PULL FAIL']:
            string_split = string.split(' ', 1)
            if len(string_split) is not 2:
                return False
            if string_split[0] == "PICKLE":
                #if it's a pickle
                sPickle = serialized.PickleSerialized(string_split[1])
                sPickle.addToPackage(self.es.readNetstring())
                try:
                    data = sPickle.unpack()
                except pickle.PickleError, e:
                    print "Error unpickling object: ", e
                    return False
            elif string_split[0] == 'ARRAY':
                #if it's an array
                try:
                    sArray = serialized.ArraySerialized(string_split[1])
                except NameError:
                    return False    
                for i in range(3):#arrays have a 3 line package
                    sArray.addToPackage(self.es.readNetstring())
                data = sArray.unpack()
            else:
                #we don't know how to handle it!
                return False
            
            #successful retrieval
            results.append(data)
            #get next string and reenter loop
            string = self.es.readNetstring()
            if string == "SEGMENT PULLED":
                if len(results) is 1:
                    results = results[0]
                returns.append(results)
                results = []
                string = self.es.readNetstring()
        #finish pulling
        if not returns:
            #if it was not a nested list
            returns = [results]
        if string == 'PULL OK':
            if not multitargets:
                returns = returns[0]
            elif len(keys) > 1:
                returns = zip(*returns)
            elif len(keys) is 1:
                returns = tuple(returns)
            return returns
        else:
            return False
    
    def __getitem__(self, id):
        if isinstance(id, slice):
            return RCView(self, id)
        elif isinstance(id, int):
            return EngineProxy(self, id)
        elif isinstance(id, str):
            return self.pull('all', *(id,))
        else:
            raise TypeError("__getitem__ only takes strs, ints, and slices")
    
    def pullNamespace(self, targets, *keys):
        """Gets a namespace dict with keys from targets.  This is just a wrapper
        for pull, to construct namespace dicts from the results of pull.
        
        returns:
            1 target:
                a dictionary of keys/values on remote engine
            >1 targets:
                a list of dictionaries of the form of 1 target.  Order of targets
                is maintained.
                
            """
        targetstr = self.parseTargets(targets)
        if not targetstr or not keys or not self._check_connection():
            # need something to do
            return False
        
        multitargets = self.multiTargets(targets)
        values = self.pull(targets, *keys)
        if values == False:
            # could be bad, but not *necessarily*
            if multitargets or len(keys) > 1:
                # definitely bad
                return False
            elif not self.execute(targets, ' '):
                # check bad target failure
                # probably do not want to do this 
                return False
        
        if len(keys) > 1 and multitargets:
            results = zip(*values)
        elif multitargets:
            results = values
        elif len(keys) > 1:
            results = [values]
        else:
            dikt = {}
            dikt[keys[0]] = values
            return dikt
        returns = []
        for r in results:
            dikt = {}
            if len(keys) == 1:
                kv = ((keys[0], r),)
            else:
                kv = zip(keys, r)
            for k,v in kv:
                dikt[k] = v
            returns.append(dikt)
        if not multitargets:
            returns = returns[0]
        return returns
    
    def scatter(self, targets, key, seq, style='basic', flatten=False):
        """distribute sequence object to targets"""
        targetstr = self.parseTargets(targets)
        if not targetstr or not key  or not self._check_connection()\
                or not isinstance(seq, (tuple, list)+arraytypes):
            return False
        
        try:
            serial = serialized.serialize(seq, key)
        except:
            return False
        string = 'SCATTER style=%s flatten=%i::%s' %(
                        style, int(flatten), targetstr)
        try:
            self.es.writeNetstring(string)
        except socket.error:
            try:
                self.connect()
                self.es.writeNetstring(string)
            except socket.error:
                return False
        
        self.sendSerialized(serial)
        reply = self.es.readNetstring()
        if reply == 'SCATTER OK':
            return True
        else:
            return False
    
    def gather(self, targets, key, style='basic'):
        """gather a distributed object, and reassemble it"""
        targetstr = self.parseTargets(targets)
        if not targetstr or not key or not self._check_connection():
            #need something to do
            return False
        
        string = 'GATHER %s style=%s::%s' %(key, style, targetstr)
        try:
            self.es.writeNetstring(string)
        except socket.error:
            try:
                self.connect()
                self.es.writeNetstring(string)
            except socket.error:
                return False
        
        split = self.es.readNetstring().split(' ',1)
        if len(split) is not 2:
            return False
        if split[0] == 'PICKLE':
            serial = serialized.PickleSerialized(key)
            serial.addToPackage(self.es.readNetstring())
            try:
                obj = serial.unpack()
            except pickle.PickleError, e:
                print 'could not unpickle: ', e
                return False
        elif split[0] == 'ARRAY':
            serial = serialized.ArraySerialized(key)
            for i in range(3):
                serial.addToPackage(self.es.readNetstring())
            try:
                obj = serial.unpack()
            except Exception, e:
                print 'could not build array: ', e
                return False
        else:
            return False
        
        if self.es.readNetstring() == 'GATHER OK':
            return obj
        else:
            return False
    
    def getResult(self, targets, i=None):
        """Gets a specific result from the kernels, returned as a tuple, or 
            list of tuples if multiple targets."""
        targetstr = self.parseTargets(targets)
        if not targetstr or not self._check_connection():
            # need something to do
            return False
        
        if i is None:
            string = "GETRESULT ::%s" %targetstr
        else:
            string = "GETRESULT %i::%s" % (i, targetstr)
        try:
            self.es.writeNetstring(string)
        except socket.error:
            try:
                self.connect()
                self.es.writeNetstring(string)
            except socket.error:
                return False
        
        string = self.es.readNetstring()
        if string == "PICKLE RESULT":
            package = self.es.readNetstring()
            string = self.es.readNetstring()
            try:
                data = pickle.loads(package)
            except pickle.PickleError, e:
                print "Error unpickling object: ", e
                return False
            else:
                if string == "GETRESULT OK":
                    if not self.multiTargets(targets):
                        data = data[0]
                    return data
                else:
                    print string
                    return False
        else:
            # For other data types
            print string
            return False
    
    def status(self, targets):
        """Check the status of the kernel."""
        targetstr = self.parseTargets(targets)
        if not targetstr or not self._check_connection():
            # need something to do
            return False
        
        string = "STATUS ::%s" %targetstr
        try:
            self.es.writeNetstring(string)
        except socket.error:
            try:
                self.connect()
                self.es.writeNetstring(string)
            except socket.error:
                return False
        
        string = self.es.readNetstring()
        if string == "PICKLE STATUS":
            package = self.es.readNetstring()
            string = self.es.readNetstring()
            try:
                data = pickle.loads(package)
            except pickle.PickleError, e:
                print "Error unpickling object: ", e
                return False
            else:
                if string == "STATUS OK":
                    if not self.multiTargets(targets):
                        data = data[0][1]
                    return data
                else:
                    return False
        else:
            return False
    
    def getIDs(self):
        if not self._check_connection():
            return False
        
        string = "GETIDS"
        try:
            self.es.writeNetstring(string)
        except socket.error:
            try:
                self.connect()
                self.es.writeNetstring(string)
            except socket.error:
                return False
        
        package = self.es.readNetstring()
        try:
            ids = pickle.loads(package)
        except pickle.PickleError:
            return False
        
        s = self.es.readNetstring()
        if s == "GETIDS OK":
            return ids
        else:
            return False
    def notify(self, addr=None, flag=True):
        """Instruct the kernel to notify a result gatherer.
        
        When the IPython kernel runs code, it traps the stdout and stderr
        of each command and stores them in a list.  The tuple of stdin, stdout
        and stderr of each executed command is called the result of the command.
        
        The result of each command is sent by the kernel to the user who 
        collects and handles the results using instances of the ResultGatherer
        class.  This class is bound to a UDP port and handles results from one
        or more kernels that are sending results to the ResultGatherer.
        
        This design was choosen to allow complete flexibility in monitoring
        the activity of groups of ipython kernels.  Each kernel keeps a list of    
        (ip, port) tuples to which results should be sent.  New addresses are
        added to this list using the notify() method.  This way each kernel can
        send results to multple observers and each observer can watch a 
        different set of kernels. 
            
        @arg addr:
            The (ip, port) tuple of the result gatherer
        @arg flag:
            A boolean to turn notification on (True) or off (False) 
        """
        if not self._check_connection():
            return False
        
        if addr is None:
            host = socket.gethostbyname(socket.gethostname())
            port = 10104
            # print "Kernel notification: ", host, port, flag
        else:
            host, port = addr
            
        if flag:
            string = "NOTIFY ADD %s %s" % (host, port)
        else:
            string = "NOTIFY DEL %s %s" % (host, port)
        try:
            self.es.writeNetstring(string)
        except socket.error:
            try:
                self.connect()
                self.es.writeNetstring(string)
            except socket.error:
                return False
        
        string = self.es.readNetstring()
        if string == "NOTIFY OK":
            return True
        else:
            return False
    
    def reset(self, targets):
        """Clear the namespace if the kernel."""
        targetstr = self.parseTargets(targets)
        if not targetstr or not self._check_connection():
            # need something to do
            return False
        
        string = "RESET ::%s" %targetstr
        try:
            self.es.writeNetstring(string)
        except socket.error:
            try:
                self.connect()
                self.es.writeNetstring(string)
            except socket.error:
                return False
        
        string = self.es.readNetstring()
        if string == "RESET OK":
            return True
        else:
            return False      
    
    def kill(self, targets):
        """Kill the engine completely."""
        targetstr = self.parseTargets(targets)
        if not targetstr or not self._check_connection():
            # need something to do
            return False
        
        self.es.writeNetstring("KILL ::%s" %targetstr)
        string = self.es.readNetstring()
        if string == "KILL OK":
            return True
        else:
            return False      
    
    def disconnect(self):
        """Disconnect from the kernel, but leave it running."""
        if self.is_connected():
            try:
                self.es.writeNetstring("DISCONNECT")
            except socket.error:
                return True
            string = self.es.readNetstring()
            if string == "DISCONNECT OK":
                self.s.close()
                del self.s
                del self.es
                return True
            else:
                return False
        else:
            return True
    
    def pushModule(self, mod):
        """Send a locally imported module to a kernel.
        
        This method makes a tarball of an imported module that exists 
        on the local host and sends it to the working directory of the
        kernel.  It then untars it.  
        
        After that, the module can be imported and used by the kernel.
        
        Notes:
        
        - It DOES NOT handle eggs yet.
        
        - The file must fit in the available RAM.
        
        - It will handle both single module files, as well as packages.
        
        - The byte code files (*.pyc) are not deleted.
        
        - It has not been tested with modules containing extension code,
          but it should work in most cases.
        
        - There are cross platform issues. 
        """
        
        tarball_name, fileString = _tar_module(mod)
        self._push_moduleString(tarball_name, fileString)
    
    def _push_moduleString(self, tarball_name, fileString):
        """This method send a tarball'd module to a kernel."""
        
        self.push('tar_fileString',fileString)
        self.execute("tar_file = open('%s','wb')" % \
            tarball_name, block=False)
        self.execute("tar_file.write(tar_fileString)", block=False)
        self.execute("tar_file.close()", block=False)
        self.execute("import os", block=False)
        self.execute("os.system('tar -xf %s')" % tarball_name)        
    

    


# The Server Side:

class NonBlockingProducer:
    """A producer for nonblocking commands.  It waits for the consumer to 
    perform its next write, then makes a callback."""
    implements(IProducer)
    
    def __init__(self, protocol):
        self.factory = protocol.factory
        self._reset()
    
    def _reset(self):
        self.consumer = None
        self.deferred = None
        self.firstCall = True
    
    def register(self, consumer, deferred):
        self.consumer = consumer
        self.deferred = deferred
        consumer.registerProducer(self, False)
    
    def resumeProducing(self):
        if self.firstCall:
            self.firstCall = False
            return
        self.deferred.callback(None)
        self.consumer.unregisterProducer()
        self._reset()
        return self.deferred
    
    def pauseProducing(self):
        pass
    
    def stopProducing(self):
        log.msg("stopped producing!")
        self._reset()
    

class VanillaControllerProtocol(protocols.EnhancedNetstringReceiver):
    """The control protocol for the Controller.  It listens for clients to
    connect, and relays commands to the controller service.
    A line based protocol."""
    
    nextHandler = None
    def connectionMade(self):
        log.msg("Connection Made...")
        self.transport.setTcpNoDelay(True)
        self.producer = NonBlockingProducer(self)
        self._reset()
    
    
    def connectionLost(self, reason):
        print reason
    def stringReceived(self, string):
        if self.nextHandler is None:
            self.defaultHandler(string)
        else:
            self.nextHandler(string)
    
    def dispatch(self, string):
        splitString = string.split(" ", 1)
        cmd = splitString[0]
        if len(splitString) is 1:
            args = None
            targets = 'all'
        elif len(splitString) is 2:
            arglist = splitString[1].split('::')
            args = arglist[0]
            if len(arglist) > 1:
                targets = self.parseTargets(arglist[1:])
                if not self.factory.verifyTargets(targets):
                    self._reset()
                    self.sendString("BAD ID LIST")
                    return
            else:
                targets = 'all'
        f = getattr(self, 'handle_%s' %(cmd), None)
        if f:
            # Handler resolved with state and cmd 
            f(args, targets)
        else:
            self._reset()
            self.sendString("BAD COMMAND")
    
    def handleUnexpectedData(self, args):
        self.sendString('UNEXPECTED DATA')
    
    defaultHandler = handleUnexpectedData
    
    def _reset(self):
        self.workVars = {}
        self.nextHandler = self.dispatch
    
    def parseTargets(self, targetsList):
        
        if len(targetsList) is 0:
            return 'all'
        else:
            if targetsList[0] == 'all':
                return 'all'
            try:
                return map(int, targetsList)
            except:
                #defaults to all on bad targetList  should it do this
                return None
    
    #####   
    ##### The GETIDS command
    #####
    
    def handle_GETIDS(self, args, targets):
        d = self.factory.getIDs()
        return d.addCallbacks(self.getIDsCallback, self.getIDsFail)
    
    def getIDsCallback(self, idlist):
        try:
            s = pickle.dumps(idlist, 2)
        except pickle.PickleError:
            self.getIDsFail()
        self.sendString(s)
        self.sendString("GETIDS OK")
    
    def getIDsFail(self, f):
        self.sendString("GETIDS FAIL")
    
    #####   
    ##### The PUSH command
    #####
    
    def handle_PUSH(self, args, targets):
        self.nextHandler = self.handlePushing
        self.workVars['pushTargets'] = targets
        self.workVars['pushDict'] = {}
        self.sendString("PUSH READY")
    
    def handlePushing(self, args):
        if args == "PUSH DONE":
            return self.handlePushingDone()
        arglist = args.split(' ',1)
        if len(arglist) is 2:
            pushType = arglist[0]
            self.workVars['pushKey'] = arglist[1]
        else:
            self.pushFinish("FAIL")
            return
        
        f = getattr(self, 'handlePushing_%s' %pushType, None)
        if f is not None:
            self.nextHandler = f
        else:
            self.pushFinish("FAIL")
    
    def handlePushing_PICKLE(self, package):
        self.nextHandler = self.handlePushing
        key = self.workVars['pushKey']
        serial = serialized.PickleSerialized(key)
        serial.addToPackage(package)
        self.workVars['pushDict'][key] = serial
    
    def handlePushing_ARRAY(self, pShape):
        self.nextHandler = self.handlePushingArray_dtype
        key = self.workVars['pushKey']
        serial = serialized.ArraySerialized(key)
        serial.addToPackage(pShape)
        self.workVars['pushSerial'] = serial
    
    def handlePushingArray_dtype(self, dtype):
        self.nextHandler = self.handlePushingArray_buffer
        self.workVars['pushSerial'].addToPackage(dtype)
    
    def handlePushingArray_buffer(self, arrayBuffer):
        self.nextHandler = self.handlePushing
        key = self.workVars['pushKey']
        self.workVars['pushSerial'].addToPackage(arrayBuffer)
        self.workVars['pushDict'][key] = self.workVars['pushSerial']
    
    def handlePushingDone(self):
        self.nextHandler = self.handleUnexpectedData
        d = defer.Deferred().addCallback(self.pushCallback)
        self.producer.register(self.transport, d)
        self.sendString('PUSH OK')
        return d
    
    def pushCallback(self, _):
        dikt = self.workVars['pushDict']
        targets = self.workVars['pushTargets']
        self._reset()
        return self.factory.pushSerialized(targets, 
                    **dikt)
    
    def pushFinish(self,msg):
        self._reset()
        self.sendString("PUSH %s" % msg)
    
    #####
    ##### The PULL command
    #####
    
    def handle_PULL(self, args, targets):
        # Parse the args
        try:
            self.workVars['pullKeys'] = args.split(',')
        except TypeError:
            self.pullFinish('FAIL')
        else:
            self.nextHandler = self.handleUnexpectedData
            d = self.factory.pullSerialized(targets, *self.workVars['pullKeys'])
            d.addCallbacks(self.pullOK, self.pullFail)
            return d
    
    def pullOK(self, entireResultList):
        for perTargetResultList in entireResultList:
            if len(self.workVars['pullKeys']) == 1:
                perTargetResultList = [perTargetResultList]
            for serialResult in perTargetResultList:
                if not isinstance(serialResult, serialized.Serialized):
                    try:
                        serialResult = serialized.serialize(serialResult, '_')
                    except:
                        self.pullFail()
                self.sendSerialized(serialResult)
            
            self.sendString("SEGMENT PULLED")
        self.pullFinish("OK")
    
    def sendPickleSerialized(self, p):
            for line in p:
                self.sendString(line)
    
    def sendArraySerialized(self, a):
        for line in a[:-1]:
            self.sendString(line)
        self.sendBuffer(a[-1])
    
    def sendSerialized(self, s):
        maxlen = max(map(len, [line for line in s]))
        if maxlen > self.MAX_LENGTH:
            e = protocols.MessageSizeError(s.key)
            f = serialized.serialize(Failure(e), 'FAILURE')
            maxlen = max(map(len, [line for line in f]))
            if maxlen > self.MAX_LENGTH:
                return self.transport.loseConnection()
            return self.sendSerialized(f)
        
        if isinstance(s, serialized.PickleSerialized):
            self.sendPickleSerialized(s)
        elif isinstance(s, serialized.ArraySerialized):
            self.sendArraySerialized(s)
    
    def pullFail(self, failure):
        self.pullFinish("FAIL")
    
    def pullFinish(self, msg):
        self._reset()
        self.sendString("PULL %s" % msg)
    
    
    #####
    ##### The SCATTER command
    #####
    
    def handle_SCATTER(self, args, targets):
        if not args:
            self.nextHandler = self.handleScatter
            return
        argSplit = args.split(' ',1)
        self.workVars['scatterTargets'] = targets
        for a in argSplit:
            split = a.split('=',1)
            if len(split) is 2:
                if split[0] == 'style':
                    self.workVars['scatterStyle'] = split[1]
                elif split[0] == 'flatten':
                    self.workVars['scatterFlatten'] = int(split[1])
                else:
                    self.scatterFail()
                    return
            else:
                self.scatterFail()
                return
        self.nextHandler = self.handleScatter
    
    def handleScatter(self, args):
        arglist = args.split(' ',1)
        if len(arglist) is 2:
            scatterType = arglist[0]
            self.workVars['scatterKey'] = arglist[1]
        else:
            self.scatterFinish("FAIL")
            return
        
        f = getattr(self, 'handleScatter_%s' %scatterType, None)
        if f is not None:
            self.nextHandler = f
        else:
            self.scatterFinish("FAIL")
    
    def handleScatter_PICKLE(self, package):
        self.nextHandler = self.handleUnexpectedData
        key = self.workVars['scatterKey']
        serial = serialized.PickleSerialized(key)
        serial.addToPackage(package)
        self.workVars['scatterSerial'] = serial
        return self.handleScatterDone()
    
    def handleScatter_ARRAY(self, pShape):
        self.nextHandler = self.handleScatterArray_dtype
        key = self.workVars['scatterKey']
        serial = serialized.ArraySerialized(key)
        serial.addToPackage(pShape)
        self.workVars['scatterSerial'] = serial
    
    def handleScatterArray_dtype(self, dtype):
        self.nextHandler = self.handleScatterArray_buffer
        self.workVars['scatterSerial'].addToPackage(dtype)
    
    def handleScatterArray_buffer(self, arrayBuffer):
        self.nextHandler = self.handleUnexpectedData
        key = self.workVars['scatterKey']
        self.workVars['scatterSerial'].addToPackage(arrayBuffer)
        return self.handleScatterDone()
    
    def handleScatterDone(self):
        d = defer.Deferred().addCallback(self.scatterCallback)
        self.producer.register(self.transport, d)
        self.sendString('SCATTER OK')
        return d
    
    def scatterCallback(self, _):
        key = self.workVars['scatterKey']
        targets = self.workVars['scatterTargets']
        obj = self.workVars['scatterSerial'].unpack()
        kw = {}
        style = self.workVars.get('scatterStyle', None)
        if style is not None:
            kw['style'] = style
        flatten = self.workVars.get('scatterFlatten', None)
        if flatten is not None:
            kw['flatten'] = flatten
        self._reset()
        return self.factory.scatter(targets, key, obj, **kw)
    
    def scatterFail(self, failure=None):
        self.scatterFinish("FAIL")
    
    def scatterFinish(self, msg):
        self._reset()
        self.sendString("SCATTER "+ msg)
    
    
    #####
    ##### The GATHER command
    #####
    
    def handle_GATHER(self, args, targets):
        # Parse the args
        if not args:
            self.gatherFail()
        
        argSplit = args.split(' ',1)
        self.workVars['gatherKey'] = argSplit[0]
        kw = {}
        if len(argSplit) is 2:
            styleSplit = argSplit[1].split('=',1)
            if styleSplit[0] == 'style' and len(styleSplit) is 2:
                kw['style'] = styleSplit[1]
        self.nextHandler = self.handleUnexpectedData
        d = self.factory.gather(targets, self.workVars['gatherKey'], **kw)
        d.addCallbacks(self.gatherOK, self.gatherFail)
        return d
    
    def gatherOK(self, obj):
        try:
            serial = serialized.serialize(obj, self.workVars['gatherKey'])
            self.sendSerialized(serial)
        except:
            self.gatherFail(Failure())
        self.gatherFinish("OK")
    
    def gatherFail(self, failure=None):
        self.gatherFinish("FAIL")
    
    def gatherFinish(self, msg):
        self._reset()
        self.sendString("GATHER %s" % msg)
    
    
    #####
    ##### The EXECUTE command
    #####
    
    def handle_EXECUTE(self, args, targets):
        """Handle the EXECUTE command."""
                
        # Parse the args
        if not args:
            self.executeFinish("FAIL")
            return
        
        if args[:5] == "BLOCK":
            block = True
            execute_cmd = args[6:]
        else:
            block = False
            execute_cmd = args
        
        if not execute_cmd:
            self.executeFinish("FAIL")
            return
        
        self.nextHandler = self.handleUnexpectedData

        if block:
            d = self.factory.execute(targets,execute_cmd)
            d.addCallback(self.executeBlockOK)
            d.addErrback(self.executeFail)
        else:
            self.workVars['execute_cmd'] = execute_cmd
            self.workVars['execute_targets'] = targets
            d = defer.Deferred().addCallback(self.executeCallback)
            self.producer.register(self.transport, d)
            self.sendString('EXECUTE OK')
            return d
    
    def executeCallback(self, _):
        execute_cmd = self.workVars['execute_cmd']
        targets = self.workVars['execute_targets']
        self._reset()
        return self.factory.execute(targets, execute_cmd)
    
    def executeBlockOK(self, results):
        for r in results:
            try:
                if isinstance(r, Failure):
                    serial = serialized.serialize(r, 'FAILURE')
                else:
                    serial = serialized.serialize(r, 'RESULT')
            except pickle.PickleError, e:
                self.executeFinish("FAIL")
            else:
                self.sendSerialized(serial)
        self.executeFinish("OK")
    
    def executeFail(self, f):
        self.executeFinish("FAIL")
    
    def executeFinish(self, msg):
        self._reset()
        self.sendString("EXECUTE %s" % msg)
    
    #####
    ##### GETRESULT command
    #####
    
    def handle_GETRESULT(self, args, targets):
        
        self.nextHandler = self.handleUnexpectedData
        try: 
            index = int(args)
        except ValueError:
            index = None
        d = self.factory.getResult(targets, index)
        d.addCallbacks(self.getResultOK, self.getResultFail)
    
    def getResultOK(self, result):
        try:
            package = pickle.dumps(result, 2)
        except pickle.pickleError:
            self.getResultFinish("FAIL")
            return
        else:
            self.sendString("PICKLE RESULT")
            self.sendString(package)
            self.getResultFinish("OK")
    
    def getResultFail(self, f):
        self.getResultFinish("FAIL")
    
    def getResultFinish(self, msg):
        self._reset()
        self.sendString("GETRESULT %s" %msg)
    
    
    #####
    ##### Kernel control commands
    #####
    
    def handle_STATUS(self, args, targets):
        self.nextHandler = self.handleUnexpectedData
        d = self.factory.status(targets).addCallbacks(
            self.statusOK, self.statusFail)
        return d
    
    def statusOK(self, status):
        try:
            serial = serialized.serialize(status, 'STATUS')
        except pickle.PickleError:
            self.statusFinish('FAIL')
        else:
            self.sendSerialized(serial)
            self.statusFinish('OK')
    
    def statusFail(self, reason):
        self.statusFinish("FAIL")
    
    def statusFinish(self, msg):
        self._reset()
        self.sendString("STATUS %s" % msg)
    
    def handle_NOTIFY(self, args, targets):
        self.nextHandler = self.handleUnexpectedData
        if not args:
            self.notifyFail()
            return
        else:
            args_split = args.split(" ")
            
        if len(args_split) is 3:
            action, host, port = args_split
            try:
                port = int(port)
            except ValueError:
                self.notifyFail()
            else:
                if action == "ADD":
                    n = results.INotifierChild((host, port))
                    return self.factory.addNotifier(n
                    ).addCallbacks(self.notifyOK, self.notifyFail)
                elif action == "DEL":
                    return self.factory.delNotifier((host, port)
                    ).addCallbacks(self.notifyOK, self.notifyFail)
                else:
                    self.notifyFail()
        else:
            self.notifyFail()
    
    def notifyOK(self, s):
        self.notifyFinish("OK")
    
    def notifyFail(self, f=None):
        self.notifyFinish("FAIL")
    
    def notifyFinish(self, msg):
        self._reset()
        self.sendString("NOTIFY %s" % msg)
    # The RESET, KILL and DISCONNECT commands
    
    def handle_RESET(self, args, targets):
        self._reset()
        self.sendString('RESET OK')
        return self.factory.reset(targets)
    
    def handle_KILL(self, args, targets):
        self._reset()
        self.sendString('KILL OK')
        return self.factory.kill(targets)
    
    def handle_DISCONNECT(self, args, targets):
        log.msg("Disconnecting client...")
        self._reset()
        self.sendString("DISCONNECT OK")
        self.transport.loseConnection()
    

class IVanillaControllerFactory(Interface):
    """interface to clients for controller"""
    
    #IQueuedEngine multiplexer methods
    def cleanQueue(self, targets):
        """Cleans out pending commands in an engine's queue."""
    
    #IEngine multiplexer methods
    def execute(self, targets, lines):
        """Execute lines of Python code."""
    
    def pushSerialized(self, targets, **namespace):
        """push value into locals namespace with name key."""
    
    def pullSerialized(self, targets, *keys):
        """Gets an item out of the self.locals dict by key."""
    
    def pullNamespace(self, targets, *keys):
        """Gets an item out of the user namespace by key."""
    
    def status(self, targets):
        """status of engines"""
    
    def reset(self, targets):
        """Reset the InteractiveShell."""
    
    def kill(self, targets):
        """kill engines"""
    
    def getResult(self, targets, i=None):
        """Get the stdin/stdout/stderr of command i."""
    


class VanillaControllerFactoryFromService(protocols.EnhancedServerFactory):
    """the controller factory"""
    
    implements(IVanillaControllerFactory)
    
    protocol = VanillaControllerProtocol
    
    def __init__(self, service):
        self.service = service
    
    def addNotifier(self, n):
        return self.service.addNotifier(n)
    
    def delNotifier(self, n):
        return self.service.delNotifier(n)
    
    def verifyTargets(self, targets):
        return self.service.verifyTargets(targets)
    
    def getIDs(self):
        return self.service.getIDs()
    
    #IQueuedEngine multiplexer methods
    def cleanQueue(self, targets):
        """Cleans out pending commands in an engine's queue."""
        return self.service.cleanQueue(targets)
    
    #IEngine multiplexer methods
    def execute(self, targets, lines):
        """Execute lines of Python code."""
        d = self.service.execute(targets, lines)
        return d
        
    def pushSerialized(self, targets, **namespace):
        """Push value into locals namespace with name key."""
        return self.service.pushSerialized(targets, **namespace)
    
    def pullSerialized(self, targets, *keys):
        """Gets an item out of the user namespace by key."""
        return self.service.pullSerialized(targets, *keys)
    
    def pullNamespace(self, targets, *keys):
        """Gets an item out of the user namespace by key."""
        return self.service.pullNamespace(targets, *keys)
    
    def scatter(self, targets, key, seq, style='basic', flatten=False):
        """distribute an object across targets"""
        return self.service.scatter(targets, key, seq, style, flatten)
    
    def gather(self, targets, key, style='basic'):
        """gather and reassemble distributed object"""
        return self.service.gather(targets, key, style)
    
    def status(self, targets):
        """status of engines"""
        return self.service.status(targets)
    
    def reset(self, targets):
        """Reset the InteractiveShell."""
        return self.service.reset(targets)
    
    def kill(self, targets):
        """kill an engine"""
        return self.service.kill(targets)
    
    def getResult(self, targets, i=None):
        """Get the stdin/stdout/stderr of command i."""
        return self.service.getResult(targets, i)
    


components.registerAdapter(VanillaControllerFactoryFromService,
                        controllerservice.ControllerService,
                        IVanillaControllerFactory)
