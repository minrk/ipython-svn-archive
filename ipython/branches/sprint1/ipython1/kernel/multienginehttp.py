# encoding: utf-8
# -*- test-case-name: ipython1.test.test_multiengine -*-
"""REST web service interface to an IMultiEngine Controller
"""
__docformat__ = "restructuredtext en"
#-------------------------------------------------------------------------------
#       Copyright (C) 2005  Fernando Perez <fperez@colorado.edu>
#                           Brian E Granger <ellisonbg@gmail.com>
#                           Benjamin Ragan-Kelley <benjaminrk@gmail.com>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

import cPickle as pickle
# try:
import httplib2

from zope.interface import Interface, implements, Attribute
from twisted.internet import defer
from twisted.python import components, failure, log

from ipython1.kernel import httputil
from ipython1.external.twisted.web2 import server, channel
from ipython1.external.twisted.web2 import http, resource
from ipython1.external.twisted.web2 import responsecode, stream
from ipython1.external.twisted.web2 import http_headers

from ipython1.kernel import newserialized
from ipython1.kernel import error
from ipython1.kernel.multiengineclient import PendingResult
from ipython1.kernel.multiengineclient import ResultList, QueueStatusList
from ipython1.kernel.multiengineclient import wrapResultList
from ipython1.kernel.multiengineclient import InteractiveMultiEngineClient
from ipython1.kernel.multiengine import \
    IMultiEngine, \
    ISynchronousMultiEngine

def _printer(*args, **kwargs):
    print args,kwargs
    return args, kwargs
#-------------------------------------------------------------------------------
# The Controller/MultiEngine side of things
#-------------------------------------------------------------------------------

class IHTTPMultiEngineRoot(Interface):
    pass


class HTTPMultiEngineRoot(resource.Resource):
    
    addSlash = True
    
    def __init__(self, multiengine):
        self.smultiengine = ISynchronousMultiEngine(multiengine)
        self.child_execute = HTTPMultiEngineExecute(self.smultiengine)
        self.child_push = HTTPMultiEnginePush(self.smultiengine)
        self.child_pull = HTTPMultiEnginePull(self.smultiengine)
        self.child_getresult = HTTPMultiEngineGetResult(self.smultiengine)
        self.child_reset = HTTPMultiEngineReset(self.smultiengine)
        self.child_keys = HTTPMultiEngineKeys(self.smultiengine)
        self.child_kill = HTTPMultiEngineKill(self.smultiengine)
        self.child_clearqueue = HTTPMultiEngineClearQueue(self.smultiengine)
        self.child_queustatus = HTTPMultiEngineQueueStatus(self.smultiengine)
        self.child_scatter = HTTPMultiEngineScatter(self.smultiengine)
        self.child_gather = HTTPMultiEngineGather(self.smultiengine)
        self.child_getids = HTTPMultiEngineGetIDs(self.smultiengine)
        
        self.child_registerclient = HTTPMultiEngineRegisterClient(self.smultiengine)
        self.child_unregisterclient = HTTPMultiEngineUnregisterClient(self.smultiengine)
        
    #def locateChild(self, request, segments):
    #    log.msg("Segments: " + repr(segments))
    #    return self, ()
    
    def renderHTTP(self, request):
        return http.Response(200, stream=stream.MemoryStream(repr(request)))
    


components.registerAdapter(HTTPMultiEngineRoot,
    IMultiEngine,
    IHTTPMultiEngineRoot)

class HTTPMultiEngineBaseMethod(resource.Resource):
    
    def __init__(self, smultiengine):
        self.smultiengine = smultiengine
        log.msg("Creating child resource...")
    
    def locateChild(self, request, segments):
        return self, ()
    
    def renderHTTP(self, request):
        return http.Response(200, stream=stream.MemoryStream(repr(request)))
    
    def parseTargets(self, targets):
        if targets == 'all':
            return targets
        elif isinstance(targets, str):
            engines = self.smultiengine.getIDs()
            print engines
            try:
                target = int(targets)
            except ValueError:
                pass
            else:
                isGood = target in engines
                if isGood:
                    return target
                else:
                    return False
            targetStringList = targets.split(',')
            try:
                targetList = [int(t) for t in targetStringList]
            except ValueError:
                return False
            else:
                isGood = sum([int(t in engines) for t in targetList]) == len(targetList)
                if isGood:
                    return targetList
                else:
                    return False
        return False
    
    def buildRequestSummary(self, request):
        reply = """host: %r
port: %r
path: %r
prepath: %r
postpath: %r
args: %r
method: %r
headers: %r
""" % (request.host, request.port, request.path, request.prepath, 
       request.postpath, request.args, request.method, request.headers)
        return reply
    
    def packageSuccess(self, result):
        headers, data = httputil.serialize(result)
        response = http.Response(200, stream=stream.MemoryStream(data))
        for k, v in headers.iteritems():
            response.headers.addRawHeader(k, v)
        response.headers.setHeader('content-type', http_headers.MimeType('text', 'plain'))
        return response
    
    def packageFailure(self, f):
        f.cleanFailure()
        headers, data = httputil.serialize(f)
        response = http.Response(200, stream=stream.MemoryStream(data))
        for k, v in headers.iteritems():
            response.headers.addRawHeader(k, v)
        response.headers.setHeader('content-type', http_headers.MimeType('text', 'plain'))
        return response
    
    def _badRequest(self, request):
        e = error.ProtocolError("Improperly Formed Request: %s:%s"%(request.path,request.args))
        return self.packageFailure(failure.Failure(e))
    

class HTTPMultiEngineExecute(HTTPMultiEngineBaseMethod):
    
    def renderHTTP(self, request):
        try:
            targetsString = request.prepath[1]
            lines = request.args['lines'][0]
            clientID = int(request.args['clientid'][0])
            block = int(request.args['block'][0])
        except:
            return self._badRequest(request)
        
        targetsArg = self.parseTargets(targetsString)
        if targetsArg is not False:
            d = self.smultiengine.execute(clientID, block, targetsArg, lines)
            # d.addCallback(_printer)
            d.addCallbacks(self.packageSuccess, self.packageFailure)
            return d
        else:
            return self.packageFailure(failure.Failure(error.InvalidEngineID()))
    

class HTTPMultiEnginePush(HTTPMultiEngineBaseMethod):
    
    def renderHTTP(self, request):
        try:
            targetsString = request.prepath[1]
            clientID = int(request.args['clientid'][0])
            block = int(request.args['block'][0])
            pns = request.args['namespace'][0]
            ns = pickle.loads(pns)
        except:
            return self._badRequest(request)
        targetsArg = self.parseTargets(targetsString)
        if targetsArg is not False:
            d = self.smultiengine.push(clientID, block, targetsArg, **ns)
            d.addCallbacks(self.packageSuccess, self.packageFailure)
            return d
        else:
            return self.packageFailure(failure.Failure(error.InvalidEngineID()))
    

class HTTPMultiEnginePull(HTTPMultiEngineBaseMethod):
    
    def renderHTTP(self, request):
        try:
            targetsString = request.prepath[1]
            clientID = int(request.args['clientid'][0])
            block = int(request.args['block'][0])
            keys = pickle.loads(request.args['keys'][0])
            # print keys
        except:
            return self._badRequest(request)
        
        targetsArg = self.parseTargets(targetsString)
        if targetsArg is not False:
            d = self.smultiengine.pull(clientID, block, targetsArg, *keys)
            d.addCallbacks(self.packageSuccess, self.packageFailure)
            return d
        else:
            return self.packageFailure(failure.Failure(error.InvalidEngineID()))
    

class HTTPMultiEngineGetResult(HTTPMultiEngineBaseMethod):
    
    def renderHTTP(self, request):
        try:
            targetsString = request.prepath[1]
            clientID = int(request.args['clientid'][0])
            block = int(request.args['block'][0])
            ids = request.args['id'][0]
            if ids == 'None':
                id = None
            else:
                id = int(ids)
        except:
            return self._badRequest(request)
        targetsArg = self.parseTargets(targetsString)
        if targetsArg is not False:
            d = self.smultiengine.getResult(clientID, block, targetsArg, id)
            d.addCallbacks(self.packageSuccess, self.packageFailure)
            return d
        else:
            return self.packageFailure(failure.Failure(error.InvalidEngineID()))
    

class HTTPMultiEngineReset(HTTPMultiEngineBaseMethod):
    
    def renderHTTP(self, request):
        try:
            targetsString = request.prepath[1]
            clientID = int(request.args['clientid'][0])
            block = int(request.args['block'][0])
        except:
            return self._badRequest(request)
        targetsArg = self.parseTargets(targetsString)
        if targetsArg is not False:
            d = self.smultiengine.reset(clientID, block, targetsArg)
            d.addCallbacks(self.packageSuccess, self.packageFailure)
            return d
        else:
            return self.packageFailure(failure.Failure(error.InvalidEngineID()))
    

class HTTPMultiEngineKeys(HTTPMultiEngineBaseMethod):
    
    def renderHTTP(self, request):
        try:
            targetsString = request.prepath[1]
            clientID = int(request.args['clientid'][0])
            block = int(request.args['block'][0])
        except:
            return self._badRequest(request)
        targetsArg = self.parseTargets(targetsString)
        if targetsArg is not False:
            d = self.smultiengine.keys(clientID, block, targetsArg)
            d.addCallbacks(self.packageSuccess, self.packageFailure)
            return d
        else:
            return self.packageFailure(failure.Failure(error.InvalidEngineID()))
    

class HTTPMultiEngineKill(HTTPMultiEngineBaseMethod):
    
    def renderHTTP(self, request):
        try:
            targetsString = request.prepath[1]
            clientID = int(request.args['clientid'][0])
            block = int(request.args['block'][0])
        except:
            return self._badRequest(request)
        targetsArg = self.parseTargets(targetsString)
        if targetsArg is not False:
            d = self.smultiengine.kill(clientID, block, targetsArg)
            d.addCallbacks(self.packageSuccess, self.packageFailure)
            return d
        else:
            return self.packageFailure(failure.Failure(error.InvalidEngineID()))
    

class HTTPMultiEngineClearQueue(HTTPMultiEngineBaseMethod):
    
    def renderHTTP(self, request):
        try:
            targetsString = request.prepath[1]
            clientID = int(request.args['clientid'][0])
            block = int(request.args['block'][0])
        except:
            return self._badRequest(request)
        targetsArg = self.parseTargets(targetsString)
        if targetsArg is not False:
            d = self.smultiengine.clearQueue(clientID, block, targetsArg)
            d.addCallbacks(self.packageSuccess, self.packageFailure)
            return d
        else:
            return self.packageFailure(failure.Failure(error.InvalidEngineID()))
    

class HTTPMultiEngineQueueStatus(HTTPMultiEngineBaseMethod):
    
    def renderHTTP(self, request):
        try:
            targetsString = request.prepath[1]
            clientID = int(request.args['clientid'][0])
            block = int(request.args['block'][0])
        except:
            return self._badRequest(request)
        targetsArg = self.parseTargets(targetsString)
        if targetsArg is not False:
            d = self.smultiengine.queueStatus(clientID, block, targetsArg)
            d.addCallbacks(self.packageSuccess, self.packageFailure)
            return d
        else:
            return self.packageFailure(failure.Failure(error.InvalidEngineID()))
    

class HTTPMultiEngineScatter(HTTPMultiEngineBaseMethod):
    
    def renderHTTP(self, request):
        try:
            targetsString = request.prepath[1]
            clientID = int(request.args['clientid'][0])
            block = int(request.args['block'][0])
            key = request.args['key'][0]
            seq = pickle.loads(request.args['pseq'][0])
            style = request.args['style'][0]
            flatten = bool(int(request.args['flatten'][0]))
        except:
            return self._badRequest(request)
        targetsArg = self.parseTargets(targetsString)
        if targetsArg is not False:
            d = self.smultiengine.scatter(clientID, block, targetsArg,
                key, seq, style, flatten)
            d.addCallbacks(self.packageSuccess, self.packageFailure)
            return d
        else:
            return self.packageFailure(failure.Failure(error.InvalidEngineID()))
    

class HTTPMultiEngineGather(HTTPMultiEngineBaseMethod):
    
    def renderHTTP(self, request):
        try:
            targetsString = request.prepath[1]
            clientID = int(request.args['clientid'][0])
            block = int(request.args['block'][0])
            key = request.args['key'][0]
            style = request.args['style'][0]
        except:
            return self._badRequest(request)
        targetsArg = self.parseTargets(targetsString)
        if targetsArg is not False:
            d = self.smultiengine.gather(clientID, block, targetsArg, key, style)
            d.addCallbacks(self.packageSuccess, self.packageFailure)
            return d
        else:
            return self.packageFailure(failure.Failure(error.InvalidEngineID()))
    


class HTTPMultiEngineGetIDs(HTTPMultiEngineBaseMethod):
    
    def renderHTTP(self, request):
        d = self.smultiengine.getIDs()
        d.addCallbacks(self.packageSuccess, self.packageFailure)
        return d
    

class HTTPMultiEngineRegisterClient(HTTPMultiEngineBaseMethod):
    
    def renderHTTP(self, request):
        clientID = self.smultiengine.registerClient()
        return self.packageSuccess(clientID)
    

class HTTPMultiEngineUnregisterClient(HTTPMultiEngineBaseMethod):
    
    def http_POST(request):
        clientID = request.args.get('clientid')
    


class IHTTPMultiEngineFactory(Interface):
    pass

    
def HTTPServerFactoryFromMultiEngine(multiengine):
    """Adapt an IMultiEngine to a HTTPServerFactory."""
    s = server.Site(IHTTPMultiEngineRoot(multiengine))
    return channel.HTTPFactory(s)


    
components.registerAdapter(HTTPServerFactoryFromMultiEngine,
            IMultiEngine, IHTTPMultiEngineFactory)
        

#-------------------------------------------------------------------------------
# The Client side of things
#-------------------------------------------------------------------------------
# components.

class HTTPMultiEngineClient(object):
    """Client that talks to a IMultiEngine adapted controller over HTTP.
    
    This class is usually aliased to RemoteController in ipython1.kernel.api
    so create one like this:
    
    >>> import ipython1.kernel.api as kernel
    >>> rc = kernel.RemoteController(('myhost.work.com', 8000))
    
    This class has a attribute named block that controls how most methods
    work.  If block=True (default) all methods will actually block until
    their action has been completed.  Then they will return their result
    or raise any Exceptions.  If block=False, the method will simply
    return a `PendingResult` object whose `getResult` method or `r` attribute
    can then be used to later retrieve the result.
    """
    
    def __init__(self, addr):
        """Create a client that will connect to addr.
        
        Once created, this class will autoconnect and reconnect to the
        controller as needed.
        
        :Parameters:
            addr : tuple
                The (ip, port) of the IMultiEngine adapted controller.
        """
        self.addr = addr
        self.url = 'http://%s:%s/' % self.addr
        self._server = httplib2.Http()
        self.block = True
        self._clientID = None
    
    #---------------------------------------------------------------------------
    # Non interface methods
    #---------------------------------------------------------------------------
        
    def _reallyBlock(self, block=None):
        if block is None:
            return self.block
        else:
            if block in (True, False):
                return block
            else:
                raise ValueError("block must be True or False")
    
    def htmlTargetString(self, targets):
        if targets == 'all':
            return targets
        elif isinstance(targets, (tuple, list)):
            return ','.join(targets)
        elif isinstance(targets, int):
            return str(targets)
        raise error.InvalidEngineID(str(targets))
    
    def htmlArgString(self, dikt):
        s = '?'
        for k,v in dikt.iteritems():
            if isinstance(v, str):
                vs = v
            elif isinstance(v, bool):
                if v:
                    vs = '1'
                else:
                    vs = '0'
            elif isinstance(v, (int, float, type(None))):
                vs = str(v)
            else:
                vs = pickle.dumps(v,2)
            s += k+'='+vs+'&'
        return s[:-1]
        
    def fixSpecials(self, s):
        s = s.replace(' ','%20')
        return s
    
    def _executeRemoteMethod(self, method, targets, **kwargs):
        request = self.url+method+'/'+self.htmlTargetString(targets)+self.htmlArgString(kwargs)
        request = self.fixSpecials(request)
        header, response = self._server.request(request)
        # print request
        # print header
        # print response
        result = self._unpackageResult(header, response)
        return result

    def _unpackageResult(self, header, response):
        if header['status'] == '200':
            result = pickle.loads(response)
            return self._returnOrRaise(result)
        else:
            raise error.ProtocolError("request failed: %s"%response)
        
    def _returnOrRaise(self, result):
        if isinstance(result, failure.Failure):
            result.raiseException()
        else:
            return result
        
    def _checkClientID(self):
        if self._clientID is None:
            self._getClientID()
            
    def _getClientID(self):
        header, response = self._server.request(self.url+'registerclient')
        self._clientID = self._unpackageResult(header, response)
    
    def _getPendingResult(self, resultID, block=True):
        self._checkClientID()
        return self._executeRemoteMethod('getpendingresult',
            clientid=self._clientID, resultid=resultID, block=block)
    
    #---------------------------------------------------------------------------
    # Methods to help manage pending results
    #--------------------------------------------------------------------------- 
     
    def barrier(self):
        """Synchronize and flush all `PendingResults`.
        
        This method is a synchronization primitive that waits for all existing
        `PendingResult` that a controller knows about to complete and then 
        flushes them.  More specifically, three things happen:
        
        * Wait for all `PendingResult`s to complete.
        * Raise any Exceptions that occured in the `PendingResult`s.
        * Flush the `PendingResult`s from the controller.
        
        If there are multiple Exceptions, only the first is raised.  
        
        The flush step is extremely important!  If you have a `PendingResult` object
        and then call `barrier`, further calls to `PendingResult.getResult` will
        fail as the controller no longer knows about the `PendingResult`:
        
        >>> pr = rc.executeAll('a=5',block=False)
        >>> rc.barrier()
        >>> pr.getResult()           # This will fail as pr has been flushed.
        
        Thus the `barrier` method should be used when you need to make sure that all
        `PendingResult`s have completed and check for errors.  If you actually
        need to access the results of those `PendingResult`s, you should not
        call `barrier`.  Instead, call `PendingResult.getResult` on each object.
        """
        self._checkClientID()
        # Optimize to not bring back all results
        result = self._executeRemoteMethod('getallpendingresults', clientid=self._clientID)
        for r in result:
            if isinstance(r, failure.Failure):
                r.raiseException()
        
    #---------------------------------------------------------------------------
    # IEngineMultiplexer related methods
    #---------------------------------------------------------------------------
        
    def execute(self, targets, lines, block=None):
        """Execute lines of code on targets and possibly block.
        
        :Parameters:
            targets : int, list or 'all'
                The engine ids the action will apply to.  Call `getIDs` to see
                a list of currently available engines. 
            lines : str
                A string of Python code to execute.
            block : boolean
                Should I block or not.  If block=True, wait for the action to
                complete and return the result.  If block=False, return a
                `PendingResult` object that can be used to later get the
                result.  If block is not specified, the block attribute 
                will be used instead.
            
        :Returns: A list of dictionaries with the stdin/stdout/stderr of the 
        command on each targets.
        """
        self._checkClientID()
        localBlock = self._reallyBlock(block)
        result = self._executeRemoteMethod('execute', targets, 
                clientid=self._clientID, block=localBlock, lines=lines)
        if not localBlock:
            result = PendingResult(self, result)
            result.addCallback(wrapResultList)
        else:
            result = ResultList(result)
        return result
    
    def executeAll(self, lines, block=None):
        """Execute lines of code on all targets.
        
        See the docstring for `execute` for full details.
        """
        return self.execute('all', lines, block)
    
    def push(self, targets, **namespace):
        """Push Python objects by key to targets.
        
        This method takes all key/value pairs passed in as keyword arguments
        and pushes (sends) them to the engines specified in targets.  Most Python objects
        are pickled, but numpy arrays are send using their raw buffers.
        
        :Parameters:
            targets : int, list or 'all'
                The engine ids the action will apply to.  Call `getIDs` to see
                a list of currently available engines.
            namespace : dict
                The keyword arguments of that contain the key/value pairs
                that will be pushed.
                
        Examples
        ========
        
        >>> rc.push('all', a=5)    # pushes 5 to all engines as 'a'
        >>> rc.push(0, b=30)       # pushes 30 to 0 as 'b'
        """
        
        self._checkClientID()
        # binPackage = xmlrpc.Binary(pickle.dumps(namespace, 2))
        localBlock = self._reallyBlock()
        result = self._executeRemoteMethod('push', targets, 
            clientid=self._clientID, block=localBlock, namespace=namespace)
        if not localBlock:
            result = PendingResult(self, result)
        return result
                
    def pushAll(self, **ns):
        """Push Python objects by key to all targets.
        
        See the docstring for `push` for full details.
        """
        return self.push('all', **ns)
    
    def pull(self, targets, *keys):
        """Pull Python objects by key from targets.
        
        This method gets the Python objects specified in keys from the engines specified
        in targets.
        
        :Parameters:
            targets : int, list or 'all'
                The engine ids the action will apply to.  Call `getIDs` to see
                a list of currently available engines.
            keys: list or tuple of str
                A list of variable names as string of the Python objects to be pulled
                back to the client.
                
        :Returns: A list of pulled Python objects for each target.
        
        Examples
        ========
        
        >> rc.pullAll('a')
        [10,10,10,10]
        """
        self._checkClientID()
        localBlock = self._reallyBlock()
        result = self._executeRemoteMethod('pull', targets, 
            clientid=self._clientID, block=localBlock, keys=keys)
        if not localBlock:
            result = PendingResult(self, result)
        return result
    
    def pullAll(self, *keys):
        """Pull Python objects by key from all targets.
        
        See the docstring for `pull` for full details.
        """
        return self.pull('all', *keys)
        
    def getResult(self, targets, i=None):
        """Get the stdin/stdout/stderr of a previously executed command on targets.
        
        :Parameters:
            targets : int, list or 'all'
                The engine ids the action will apply to.  Call `getIDs` to see
                a list of currently available engines.
            i : None or int
                The command number to retrieve.  The default will retrieve the most recent
                command.
                
        :Returns: The result dict for the command.
        """
        self._checkClientID()
        localBlock = self._reallyBlock()
        result = self._executeRemoteMethod('getresult', targets, 
                clientid=self._clientID, block=localBlock, id=i)
        if not localBlock:
            result = PendingResult(self, result)
            result.addCallback(wrapResultList)
        else:
            result = ResultList(result)
        return result
         
    def getResultAll(self, i=None):
        """Get the stdin/stdout/stderr of a previously executed command on all targets.
        
       See the docstring for `getResult` for full details.     
        """
        return self.getResult('all', i)
    
    def reset(self, targets):
        """Reset the namespace on targets.
        
        This method resets the persistent namespace in which computations are done in the
        each engine.  This is is sort of like a soft reset.  Use `kill` to actually stop
        the engines.
        
        :Parameters:
            targets : int, list or 'all'
                The engine ids the action will apply to.  Call `getIDs` to see
                a list of currently available engines.
        """
        self._checkClientID()
        localBlock = self._reallyBlock()
        result = self._executeRemoteMethod('reset', targets, 
                clientid = self._clientID, block=localBlock)
        if not localBlock:
            result = PendingResult(self, result)
        return result    
        
    def resetAll(self):
        """Reset the namespace on all targets.
        
       See the docstring for `reset` for full details.         
        """
        return self.reset('all')
    
    def keys(self, targets):
        """List all the variable names defined on each target.
        
        :Parameters:
            targets : int, list or 'all'
                The engine ids the action will apply to.  Call `getIDs` to see
                a list of currently available engines.
        
        :Returns: A list of the variables names on each engine.
        """
        
        self._checkClientID()
        localBlock = self._reallyBlock()
        result = self._executeRemoteMethod('keys', targets, 
                clientid = self._clientID, block=localBlock)
        if not localBlock:
            result = PendingResult(self, result)
        return result 
          
    def keysAll(self):
        """List all the variable names defined on each engine/target.
        
        See the docstring for `keys` for full details.         
        """
        return self.keys('all')
    
    def kill(self, targets, controller=False):
        """Kill the engines/targets specified.
        
        This actually stops the engine processes for good.
        
        :Parameters:
            targets : int, list or 'all'
                The engine ids the action will apply to.  Call `getIDs` to see
                a list of currently available engines.
            controller : boolean
                Kill the controller process as well?
        """
        self._checkClientID()
        localBlock = self._reallyBlock()
        result = self._executeRemoteMethod('kill', targets, 
            clientid=self._clientID, block=localBlock, controller=controller)
        if not localBlock:
            result = PendingResult(self, result)
        return result
    
    def killAll(self, controller=False):
        """Kill all the engines/targets.
        
        See the docstring for `kill` for full details.
        """
        return self.kill('all', controller)
        
    def clearQueue(self, targets):
        """Clear the command queue on targets.
        
        Each engine has a queue associated with it.  This queue lives in the controller
        process.  This command is used to kill all commmands that are waiting in the queue.
        These commands will then errback with `QueueCleared`.  Use `queueStatus` to see the
        commands in the queues.
        
        :Parameters:
            targets : int, list or 'all'
                The engine ids the action will apply to.  Call `getIDs` to see
                a list of currently available engines.    
        """
        
        self._checkClientID()
        result = self._executeRemoteMethod('clearQueue', targets, 
                clientid = self._clientID, block=False)
        return result
        
    def clearQueueAll(self):
        """Clear the command queue on all targets.
        
        See the docstring for `clearQueue` for full details.
        """
        return self.clearQueue('all')
    
    def queueStatus(self, targets):
        """Get the status of the command queue on targets.
        
        :Parameters:
            targets : int, list or 'all'
                The engine ids the action will apply to.  Call `getIDs` to see
                a list of currently available engines.
        
        :Returns:  A list of dicts that describe each queue.
        """
        self._checkClientID()
        result = self._executeRemoteMethod('queueStatus', targets, 
                clientid=self._clientID, block=False)
        return QueueStatusList(result)
    
    def queueStatusAll(self):
        """Get the status of the command queue on all targets/engines.
        
        See the docstring for `queueStatus` for full details.
        """
        return self.queueStatus('all')
    
    #---------------------------------------------------------------------------
    # IMultiEngine related methods
    #---------------------------------------------------------------------------
    
    def getIDs(self):
        """Get a list of the ids of the engines that are registered."""
        self._checkClientID()
        return self._executeRemoteMethod('getids', clientid=self._clientID, block=False)
    
    #---------------------------------------------------------------------------
    # IEngineCoordinator related methods
    #---------------------------------------------------------------------------
    
    def scatter(self, targets, key, seq, style='basic', flatten=False):
        """Partition and distribute a sequence to a set of targets/engines.
        
        This method partitions a Python sequence and then pushes the partitions
        to a set of engines.
        
        :Parameters:
            targets : int, list or 'all'
                The engine ids the action will apply to.  Call `getIDs` to see
                a list of currently available engines.
            key : str
                What to call the partitions on the engines.
            seq : list, tuple or numpy array
                The sequence to be partitioned and pushed.
            style : str
                The style of partitioning to use.  Only 'basic' is supported
            flatten : boolean
                Should length 1 partitions be flattened to scalars upon pushing.
        """
        self._checkClientID()
        # bseq = xmlrpc.Binary(pickle.dumps(seq,2))
        localBlock = self._reallyBlock()
        result = self._executeRemoteMethod('scatter', targets, 
            clientid=self._clientID, block=localBlock, key=key, seq=seq, 
            style=style, flatten=flatten)
        if not localBlock:
            result = PendingResult(self, result)
        return result
        
    def scatterAll(self, key, seq, style='basic', flatten=False):
        """Partition and distribute a sequence to all targets/engines.
        
        See the docstring for `scatter` for full details.
        """
        return self.scatter('all', key, seq, style, flatten)
    
    def gather(self, targets, key, style='basic'):
        """Gather a set of sequence partitions that are distributed on targets.
        
        This method is the inverse of `scatter` and gather parts of an overall
        sequence that are distributed among the engines and reassembles the 
        partitions into a single sequence which is returned.
        
        :Parameters:
            targets : int, list or 'all'
                The engine ids the action will apply to.  Call `getIDs` to see
                a list of currently available engines.
            key : str
                The name of the sequences on the engines.
            style : str
                Only 'basic' is supported currently.
                
        :Returns:  The reassembled sequence.
        """
        self._checkClientID()
        localBlock = self._reallyBlock()
        result = self._executeRemoteMethod('gather', targets, 
            clientid=self._clientID, block=localBlock, key=key, style=style)
        if not localBlock:
            result = PendingResult(self, result)
        return result        
        
    def gatherAll(self, key, style='basic'):
        """Gather a set of sequence partitions that are distributed on all targets.
        
        See the docstring for `gather` for full details.
        """
        return self.gather('all', key, style)


class HTTPInteractiveMultiEngineClient(HTTPMultiEngineClient, InteractiveMultiEngineClient):
    
    __doc__ = HTTPMultiEngineClient.__doc__
    
    def __init__(self, addr):
        HTTPMultiEngineClient.__init__(self, addr)
        InteractiveMultiEngineClient.__init__(self)

    __init__.__doc__ = HTTPMultiEngineClient.__init__.__doc__
    
