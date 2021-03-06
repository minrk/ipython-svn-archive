# encoding: utf-8
# -*- test-case-name: ipython1.kernel.test.test_multiengine -*-
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
import httplib2, urllib

from zope.interface import Interface, implements
from twisted.internet import defer
from twisted.python import components, failure, log

from ipython1.kernel import httputil
from ipython1.external.twisted.web2 import server, channel
from ipython1.external.twisted.web2 import http, resource
from ipython1.external.twisted.web2 import stream
from ipython1.external.twisted.web2 import http_headers

# from ipython1.kernel import newserialized
from ipython1.kernel import error
from ipython1.kernel.multiengineclient import PendingResult
from ipython1.kernel.multiengineclient import ResultList, QueueStatusList
from ipython1.kernel.multiengineclient import wrapResultList
from ipython1.kernel.multiengineclient import InteractiveMultiEngineClient
from ipython1.kernel.multiengineclient import MultiEngineCoordinator
from ipython1.kernel.multiengine import \
    IMultiEngine, \
    ISynchronousMultiEngine

def _printer(r):
    print r
    return r
#-------------------------------------------------------------------------------
# The Controller/MultiEngine side of things
#-------------------------------------------------------------------------------

class IHTTPMultiEngineRoot(Interface):
    pass


class HTTPMultiEngineRoot(resource.Resource):
    implements(IHTTPMultiEngineRoot)
    addSlash = True
    
    def __init__(self, multiengine):
        self.smultiengine = ISynchronousMultiEngine(multiengine)
        self.child_execute = HTTPMultiEngineExecute(self.smultiengine)
        self.child_push = HTTPMultiEnginePush(self.smultiengine)
        self.child_pull = HTTPMultiEnginePull(self.smultiengine)
        self.child_get_result = HTTPMultiEngineGetResult(self.smultiengine)
        self.child_reset = HTTPMultiEngineReset(self.smultiengine)
        self.child_keys = HTTPMultiEngineKeys(self.smultiengine)
        self.child_kill = HTTPMultiEngineKill(self.smultiengine)
        self.child_clear_queue = HTTPMultiEngineClearQueue(self.smultiengine)
        self.child_queue_status = HTTPMultiEngineQueueStatus(self.smultiengine)
        self.child_get_properties = HTTPMultiEngineGetProperties(self.smultiengine)
        self.child_get_ids = HTTPMultiEngineGetIDs(self.smultiengine)
        
        self.child_get_properties = HTTPMultiEngineGetProperties(self.smultiengine)
        self.child_set_properties = HTTPMultiEngineSetProperties(self.smultiengine)
        self.child_has_properties = HTTPMultiEngineHasProperties(self.smultiengine)
        self.child_del_properties = HTTPMultiEngineDelProperties(self.smultiengine)
        self.child_clear_properties = HTTPMultiEngineClearProperties(self.smultiengine)
        
        
        self.child_getPendingResult = HTTPMultiEngineGetPendingResult(self.smultiengine)
        self.child_getAllPendingResults = HTTPMultiEngineGetAllPendingResults(self.smultiengine)
        self.child_registerClient = HTTPMultiEngineRegisterClient(self.smultiengine)
        self.child_unregisterClient = HTTPMultiEngineUnregisterClient(self.smultiengine)
        
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
            engines = self.smultiengine.get_ids()
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
            clientID = int(request.args['clientID'][0])
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
            clientID = int(request.args['clientID'][0])
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
            clientID = int(request.args['clientID'][0])
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
            clientID = int(request.args['clientID'][0])
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
            d = self.smultiengine.get_result(clientID, block, targetsArg, id)
            d.addCallbacks(self.packageSuccess, self.packageFailure)
            return d
        else:
            return self.packageFailure(failure.Failure(error.InvalidEngineID()))
    

class HTTPMultiEngineReset(HTTPMultiEngineBaseMethod):
    
    def renderHTTP(self, request):
        try:
            targetsString = request.prepath[1]
            clientID = int(request.args['clientID'][0])
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
            clientID = int(request.args['clientID'][0])
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
            clientID = int(request.args['clientID'][0])
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
            clientID = int(request.args['clientID'][0])
            block = int(request.args['block'][0])
        except:
            return self._badRequest(request)
        targetsArg = self.parseTargets(targetsString)
        if targetsArg is not False:
            d = self.smultiengine.clear_queue(clientID, True, targetsArg)
            d.addCallbacks(self.packageSuccess, self.packageFailure)
            return d
        else:
            return self.packageFailure(failure.Failure(error.InvalidEngineID()))
    

class HTTPMultiEngineQueueStatus(HTTPMultiEngineBaseMethod):
    
    def renderHTTP(self, request):
        try:
            targetsString = request.prepath[1]
            clientID = int(request.args['clientID'][0])
            block = int(request.args['block'][0])
        except:
            return self._badRequest(request)
        targetsArg = self.parseTargets(targetsString)
        if targetsArg is not False:
            d = self.smultiengine.queue_status(clientID, True, targetsArg)
            # d.addBoth(_printer)
            d.addCallbacks(self.packageSuccess, self.packageFailure)
            return d
        else:
            return self.packageFailure(failure.Failure(error.InvalidEngineID()))
    

class HTTPMultiEngineSetProperties(HTTPMultiEngineBaseMethod):
    
    def renderHTTP(self, request):
        try:
            targetsString = request.prepath[1]
            clientID = int(request.args['clientID'][0])
            block = int(request.args['block'][0])
            pns = request.args['namespace'][0]
            ns = pickle.loads(pns)
        except:
            return self._badRequest(request)
        targetsArg = self.parseTargets(targetsString)
        if targetsArg is not False:
            d = self.smultiengine.set_properties(clientID, block, targetsArg, **ns)
            d.addCallbacks(self.packageSuccess, self.packageFailure)
            return d
        else:
            return self.packageFailure(failure.Failure(error.InvalidEngineID()))
    

class HTTPMultiEngineGetProperties(HTTPMultiEngineBaseMethod):
    
    def renderHTTP(self, request):
        try:
            targetsString = request.prepath[1]
            clientID = int(request.args['clientID'][0])
            block = int(request.args['block'][0])
            keys = pickle.loads(request.args['keys'][0])
        except:
            return self._badRequest(request)
        targetsArg = self.parseTargets(targetsString)
        if targetsArg is not False:
            d = self.smultiengine.get_properties(clientID, block, targetsArg, *keys)
            # d.addBoth(_printer)
            d.addCallbacks(self.packageSuccess, self.packageFailure)
            return d
        else:
            return self.packageFailure(failure.Failure(error.InvalidEngineID()))
    

class HTTPMultiEngineHasProperties(HTTPMultiEngineBaseMethod):
    
    def renderHTTP(self, request):
        try:
            targetsString = request.prepath[1]
            clientID = int(request.args['clientID'][0])
            block = int(request.args['block'][0])
            keys = pickle.loads(request.args['keys'][0])
        except:
            return self._badRequest(request)
        targetsArg = self.parseTargets(targetsString)
        if targetsArg is not False:
            d = self.smultiengine.has_properties(clientID, block, targetsArg, *keys)
            # d.addBoth(_printer)
            d.addCallbacks(self.packageSuccess, self.packageFailure)
            return d
        else:
            return self.packageFailure(failure.Failure(error.InvalidEngineID()))
    

class HTTPMultiEngineDelProperties(HTTPMultiEngineBaseMethod):
    
    def renderHTTP(self, request):
        try:
            targetsString = request.prepath[1]
            clientID = int(request.args['clientID'][0])
            block = int(request.args['block'][0])
            keys = pickle.loads(request.args['keys'][0])
        except:
            return self._badRequest(request)
        targetsArg = self.parseTargets(targetsString)
        if targetsArg is not False:
            d = self.smultiengine.del_properties(clientID, block, targetsArg, *keys)
            # d.addBoth(_printer)
            d.addCallbacks(self.packageSuccess, self.packageFailure)
            return d
        else:
            return self.packageFailure(failure.Failure(error.InvalidEngineID()))
    

class HTTPMultiEngineClearProperties(HTTPMultiEngineBaseMethod):
    
    def renderHTTP(self, request):
        try:
            targetsString = request.prepath[1]
            clientID = int(request.args['clientID'][0])
            block = int(request.args['block'][0])
            # keys = pickle.loads(request.args['keys'][0])
        except:
            return self._badRequest(request)
        targetsArg = self.parseTargets(targetsString)
        if targetsArg is not False:
            d = self.smultiengine.clear_properties(clientID, block, targetsArg)
            # d.addBoth(_printer)
            d.addCallbacks(self.packageSuccess, self.packageFailure)
            return d
        else:
            return self.packageFailure(failure.Failure(error.InvalidEngineID()))
    

class HTTPMultiEngineGetIDs(HTTPMultiEngineBaseMethod):
    
    def renderHTTP(self, request):
        d = defer.execute(self.smultiengine.get_ids)
        d.addCallbacks(self.packageSuccess, self.packageFailure)
        return d
    


class HTTPMultiEngineGetPendingResult(HTTPMultiEngineBaseMethod):
    
    def renderHTTP(self, request):
        try:
            clientID = int(request.args['clientID'][0])
            block = int(request.args['block'][0])
            ids = request.args['resultid'][0]
            if ids == 'None':
                id = None
            else:
                id = int(ids)
        except:
            return self._badRequest(request)
        d = self.smultiengine.get_pending_deferred(clientID, id, block)
        d.addCallbacks(self.packageSuccess, self.packageFailure)
        return d
    

class HTTPMultiEngineGetAllPendingResults(HTTPMultiEngineBaseMethod):
    
    def renderHTTP(self, request):
        try:
            clientID = int(request.args['clientID'][0])
        except:
            return self._badRequest(request)
        d = self.smultiengine.getAllPendingDeferreds(clientID)
        d.addCallbacks(self.packageSuccess, self.packageFailure)
        return d
    

class HTTPMultiEngineRegisterClient(HTTPMultiEngineBaseMethod):
    
    def renderHTTP(self, request):
        clientID = self.smultiengine.registerClient()
        return self.packageSuccess(clientID)
    

class HTTPMultiEngineUnregisterClient(HTTPMultiEngineBaseMethod):
    
    def http_POST(request):
        clientID = request.args.get('clientID')
    


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

class HTTPMultiEngineClient(MultiEngineCoordinator):
    """Client that talks to a IMultiEngine adapted controller over HTTP.
    
    This class is usually aliased to RemoteController in ipython1.kernel.api
    so create one like this:
    
    >>> import ipython1.kernel.api as kernel
    >>> rc = kernel.RemoteController(('myhost.work.com', 8000))
    
    This class has a attribute named block that controls how most methods
    work.  If block=True (default) all methods will actually block until
    their action has been completed.  Then they will return their result
    or raise any Exceptions.  If block=False, the method will simply
    return a `PendingResult` object whose `get_result` method or `r` attribute
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
    
    def _executeRemoteMethod(self, method, targets='', **kwargs):
        args = urllib.urlencode(httputil.strDict(kwargs))
        if targets != '':
            targets = httputil.htmlTargetString(targets)
        request = self.url+method+'/'+targets+'?'+args
        # request = self.fixSpecials(request)
        header, response = self._server.request(request)
        # print request
        # print header
        # print response
        result = self._unpackageResult(header, response)
        return result
    
    def _unpackageResult(self, header, response):
        status = header['status']
        if status == '200':
            result = httputil.unserialize(header, response)
            return self._returnOrRaise(result)
        else:
            raise error.ProtocolError("Request Failed: %s:%s"%(status, response))
        
    def _returnOrRaise(self, result):
        if isinstance(result, failure.Failure):
            result.raiseException()
        else:
            return result
        
    def _checkClientID(self):
        if self._clientID is None:
            self._getClientID()
            
    def _getClientID(self):
        header, response = self._server.request(self.url+'registerClient')
        self._clientID = self._unpackageResult(header, response)
    
    def _getPendingResult(self, result_id, block=True):
        self._checkClientID()
        return self._executeRemoteMethod('getPendingResult',
            clientID=self._clientID, resultid=result_id, block=block)
    
    #---------------------------------------------------------------------------
    # Methods to help manage pending results
    #--------------------------------------------------------------------------- 
     
    def barrier(self, *pendingResults):
        """Synchronize a set of `PendingResults`.
        
        This method is a synchronization primitive that waits for a set of
        `PendingResult` objects to complete.  More specifically, barier does
        the following.
        
        * The `PendingResult`s are sorted by result_id.
        * The `get_result` method is called for each `PendingResult` sequentially
          with block=True.
        * If a `PendingResult` gets a result that is an exception, it is 
          trapped and can be re-raised later by calling `get_result` again.
        * The `PendingResult`s are flushed from the controller.
                
        After barrier has been called on a `PendingResult`, its results can 
        be retrieved by calling `get_result` again or accesing the `r` attribute
        of the instance.
        """
        self._checkClientID()

        # Convert to list for sorting and check class type 
        prList = list(pendingResults)
        for pr in prList:
            if not isinstance(pr, PendingResult):
                raise error.NotAPendingResult("Objects passed to barrier must be PendingResult instances")
                            
        # Sort the PendingResults so they are in order
        prList.sort()
        # Block on each PendingResult object
        for pr in prList:
            try:
                result = pr.get_result(block=True)
            except Exception:
                pass
        
    #---------------------------------------------------------------------------
    # IEngineMultiplexer related methods
    #---------------------------------------------------------------------------
        
    def execute(self, targets, lines, block=None):
        """Execute lines of code on targets and possibly block.
        
        :Parameters:
            targets : int, list or 'all'
                The engine ids the action will apply to.  Call `get_ids` to see
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
                clientID=self._clientID, block=localBlock, lines=lines)
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
                The engine ids the action will apply to.  Call `get_ids` to see
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
            clientID=self._clientID, block=localBlock, namespace=namespace)
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
                The engine ids the action will apply to.  Call `get_ids` to see
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
            clientID=self._clientID, block=localBlock, keys=keys)
        if not localBlock:
            result = PendingResult(self, result)
        return result
    
    def pullAll(self, *keys):
        """Pull Python objects by key from all targets.
        
        See the docstring for `pull` for full details.
        """
        return self.pull('all', *keys)
    
    def get_result(self, targets, i=None):
        """Get the stdin/stdout/stderr of a previously executed command on targets.
        
        :Parameters:
            targets : int, list or 'all'
                The engine ids the action will apply to.  Call `get_ids` to see
                a list of currently available engines.
            i : None or int
                The command number to retrieve.  The default will retrieve the most recent
                command.
                
        :Returns: The result dict for the command.
        """
        self._checkClientID()
        localBlock = self._reallyBlock()
        result = self._executeRemoteMethod('get_result', targets, 
                clientID=self._clientID, block=localBlock, id=i)
        if not localBlock:
            result = PendingResult(self, result)
            result.addCallback(wrapResultList)
        else:
            result = ResultList(result)
        return result
    
    def get_resultAll(self, i=None):
        """Get the stdin/stdout/stderr of a previously executed command on all targets.
        
       See the docstring for `get_result` for full details.     
        """
        return self.get_result('all', i)
    
    def reset(self, targets):
        """Reset the namespace on targets.
        
        This method resets the persistent namespace in which computations are done in the
        each engine.  This is is sort of like a soft reset.  Use `kill` to actually stop
        the engines.
        
        :Parameters:
            targets : int, list or 'all'
                The engine ids the action will apply to.  Call `get_ids` to see
                a list of currently available engines.
        """
        self._checkClientID()
        localBlock = self._reallyBlock()
        result = self._executeRemoteMethod('reset', targets, 
                clientID = self._clientID, block=localBlock)
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
                The engine ids the action will apply to.  Call `get_ids` to see
                a list of currently available engines.
        
        :Returns: A list of the variables names on each engine.
        """
        
        self._checkClientID()
        localBlock = self._reallyBlock()
        result = self._executeRemoteMethod('keys', targets, 
                clientID = self._clientID, block=localBlock)
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
                The engine ids the action will apply to.  Call `get_ids` to see
                a list of currently available engines.
            controller : boolean
                Kill the controller process as well?
        """
        self._checkClientID()
        localBlock = self._reallyBlock()
        result = self._executeRemoteMethod('kill', targets, 
            clientID=self._clientID, block=localBlock, controller=controller)
        if not localBlock:
            result = PendingResult(self, result)
        return result
    
    def killAll(self, controller=False):
        """Kill all the engines/targets.
        
        See the docstring for `kill` for full details.
        """
        return self.kill('all', controller)
    
    def clear_queue(self, targets):
        """Clear the command queue on targets.
        
        Each engine has a queue associated with it.  This queue lives in the controller
        process.  This command is used to kill all commmands that are waiting in the queue.
        These commands will then errback with `QueueCleared`.  Use `queue_status` to see the
        commands in the queues.
        
        :Parameters:
            targets : int, list or 'all'
                The engine ids the action will apply to.  Call `get_ids` to see
                a list of currently available engines.    
        """
        
        self._checkClientID()
        result = self._executeRemoteMethod('clear_queue', targets, 
                clientID = self._clientID, block=False)
        return result
    
    def clear_queueAll(self):
        """Clear the command queue on all targets.
        
        See the docstring for `clear_queue` for full details.
        """
        return self.clear_queue('all')
    
    def queue_status(self, targets):
        """Get the status of the command queue on targets.
        
        :Parameters:
            targets : int, list or 'all'
                The engine ids the action will apply to.  Call `get_ids` to see
                a list of currently available engines.
        
        :Returns:  A list of dicts that describe each queue.
        """
        self._checkClientID()
        result = self._executeRemoteMethod('queue_status', targets, 
                clientID=self._clientID, block=False)
        # print result
        return QueueStatusList(result)
    
    def queue_statusAll(self):
        """Get the status of the command queue on all targets/engines.
        
        See the docstring for `queue_status` for full details.
        """
        return self.queue_status('all')
    
    
    def set_properties(self, targets, **namespace):
        """Update the properties with key/value pairs.
        
        This method takes all key/value pairs passed in as keyword arguments
        and pushes (sends) them to the engines specified in targets.  Simple
        types are recommended (strings, numbers, etc.).
        
        :Parameters:
            targets : int, list or 'all'
                The engine ids the action will apply to.  Call `get_ids` to see
                a list of currently available engines.
            namespace : dict
                The keyword arguments of that contain the key/value pairs
                that will be pushed.
                
        Examples
        ========
        
        >>> rc.set_properties('all', a=5)    # sets e.properties['a'] = 5 on all
        >>> rc.set_properties(0, b=30)       # sets e.properties['b'] = 30 on 0
        """
        
        self._checkClientID()
        # binPackage = xmlrpc.Binary(pickle.dumps(namespace, 2))
        localBlock = self._reallyBlock()
        result = self._executeRemoteMethod('set_properties', targets, 
            clientID=self._clientID, block=localBlock, namespace=namespace)
        if not localBlock:
            result = PendingResult(self, result)
        return result
    
    def set_propertiesAll(self, **ns):
        """update properties on all targets.
        
        See the docstring for `set_properties` for full details.
        """
        return self.set_properties('all', **ns)
    
    def has_properties(self, targets, *keys):
        """check the properties dicts of engines for keys.
        
        This method gets the Python objects specified in keys from the engines specified
        in targets, returning a dict for each engine.
        
        :Parameters:
            targets : int, list or 'all'
                The engine ids the action will apply to.  Call `get_ids` to see
                a list of currently available engines.
            keys: list or tuple of str
                A list of variable names as string of the properties to be
                checked.
                
        :Returns: A list of lists of boolean values for each target.
                if no keys specified, the whole properties dict is pulled.
        
        Examples
        ========
        
        >> rc.has_propertiesAll('a', 'b')
        [[True, False],[False, True],[True, True]]
        """
        self._checkClientID()
        localBlock = self._reallyBlock()
        result = self._executeRemoteMethod('has_properties', targets, 
            clientID=self._clientID, block=localBlock, keys=keys)
        if not localBlock:
            result = PendingResult(self, result)
        return result
    
    def has_propertiesAll(self, *keys):
        """check if values exist on properties objects on all engines by keys.
        
        See the docstring for `has_properties` for full details.
        """
        return self.has_properties('all', *keys)
    
    def get_properties(self, targets, *keys):
        """Pull subdicts of properties objects on engines by keys.
        
        This method gets the Python objects specified in keys from the engines specified
        in targets, returning a dict for each engine.
        
        :Parameters:
            targets : int, list or 'all'
                The engine ids the action will apply to.  Call `get_ids` to see
                a list of currently available engines.
            keys: list or tuple of str
                A list of variable names as string of the Python objects to be pulled
                back to the client.
                
        :Returns: A list of dictionary objects for each target.
                if no keys specified, the whole properties dict is pulled.
        
        Examples
        ========
        
        >> rc.get_propertiesAll('a')
        [{'a':10},{'a':10},{'a':10}]
        """
        self._checkClientID()
        localBlock = self._reallyBlock()
        result = self._executeRemoteMethod('get_properties', targets, 
            clientID=self._clientID, block=localBlock, keys=keys)
        if not localBlock:
            result = PendingResult(self, result)
        return result
    
    def get_propertiesAll(self, *keys):
        """Pull subdicts of properties objects on all engines by keys.
        
        See the docstring for `get_properties` for full details.
        """
        return self.get_properties('all', *keys)
    
    def del_properties(self, targets, *keys):
        """remove elements from properties objects on engines by keys.
        
        :Parameters:
            targets : int, list or 'all'
                The engine ids the action will apply to.  Call `get_ids` to see
                a list of currently available engines.
            keys: list or tuple of str
                A list of property labels to be cleared
                
        :Returns: None
        
        Examples
        ========
        
        >> rc.del_propertiesAll('a')
        [None, None]
        """
        self._checkClientID()
        localBlock = self._reallyBlock()
        result = self._executeRemoteMethod('del_properties', targets, 
            clientID=self._clientID, block=localBlock, keys=keys)
        if not localBlock:
            result = PendingResult(self, result)
        return result
    
    def del_propertiesAll(self, *keys):
        """remove elements from properties objects on all engines by keys.
        
        See the docstring for `del_properties` for full details.
        """
        return self.del_properties('all', *keys)
    
    def clear_properties(self, targets):
        """clear the properties objects on engines.
        
        :Parameters:
            targets : int, list or 'all'
                The engine ids the action will apply to.  Call `get_ids` to see
                a list of currently available engines.
                
        :Returns: None for each engine
        
        Examples
        ========
        
        >> rc.clear_propertiesAll()
        [None, None, None]
        >> rc.get_propertiesAll()
        [{}, {}, {}]
        """
        self._checkClientID()
        localBlock = self._reallyBlock()
        result = self._executeRemoteMethod('clear_properties', targets, 
            clientID=self._clientID, block=localBlock)
        if not localBlock:
            result = PendingResult(self, result)
        return result
    
    def clear_propertiesAll(self, *keys):
        """clear the properties objects on all engines.
        
        See the docstring for `clear_properties` for full details.
        """
        return self.clear_properties('all', *keys)
    
    
    #---------------------------------------------------------------------------
    # IMultiEngine related methods
    #---------------------------------------------------------------------------
    
    def get_ids(self):
        """Get a list of the ids of the engines that are registered."""
        self._checkClientID()
        return self._executeRemoteMethod('get_ids', clientID=self._clientID, block=False)
    
    #---------------------------------------------------------------------------
    # IEngineCoordinator related methods
    #---------------------------------------------------------------------------
    
    def scatter(self, targets, key, seq, style='basic', flatten=False):
        """Partition and distribute a sequence to a set of targets/engines.
        
        This method partitions a Python sequence and then pushes the partitions
        to a set of engines.
        
        :Parameters:
            targets : int, list or 'all'
                The engine ids the action will apply to.  Call `get_ids` to see
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
            clientID=self._clientID, block=localBlock, key=key, seq=seq, 
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
                The engine ids the action will apply to.  Call `get_ids` to see
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
            clientID=self._clientID, block=localBlock, key=key, style=style)
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
    
