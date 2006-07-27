
"""The Twisted core of the ipython controller.

This module contains the Twisted protocols, factories, etc. used to
implement the ipython controller.  This module only contains the network related
parts of the controller.
"""
#*****************************************************************************
#       Copyright (C) 2005  Brian Granger, <bgranger@scu.edu>
#                           Fernando Perez. <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

import cPickle as pickle

from twisted.internet import protocol, defer
from twisted.protocols import basic
from twisted.python import components, log

from zope.interface import Interface, implements

from ipython1.kernel import controllerservice

class LiteralString:
    def __init__(self, size, defered):
        self.size = size
        self.data = []
        self.defer = defered
    
    def write(self, data):
        self.size -= len(data)
        passon = None
        if self.size > 0:
            self.data.append(data)
        else:
            if self.size:
                data, passon = data[:self.size], data[self.size:]
            else:
                passon = ''
            if data:
                self.data.append(data)
            if passon == '':
                self.defer.callback(''.join(self.data))
        return passon
    

class ResultReporterProtocol(protocol.DatagramProtocol):
    
    def __init__(self, result, addr):
        self.result = result
        self.addr = addr
    
    def startProtocol(self):
        package = pickle.dumps(self.result, 2)
        self.transport.write("RESULT %i %s" % (len(package), package), 
            self.addr)
        self.tried = True
    
    def datagramReceived(self,data, sending_addr):
        if sending_addr == self.addr and data == "RESULT OK":
            self.transport.stopListening()
    


class ControlTCPProtocol(basic.LineReceiver):
    
    def connectionMade(self):
        log.msg("Connection Made...")
        self.transport.setTcpNoDelay(True)
        self.state = 'init'
        self.work_vars = {}
        peer = self.transport.getPeer()
#        if not self.factory.is_allowed(peer.host):
#            log.msg("Denied Client: %s" % peer.host)
#            self.transport.loseConnection()
    
    def lineReceived(self, line):
        split_line = line.split(" ", 1)
        if len(split_line) == 1:
            cmd = split_line[0]
            args = None
            id = None
        elif len(split_line) == 2:
            cmd = split_line[0]
            arglist = split_line[1].split('::')
            if len(arglist) > 1:
                id = self.parseID(arglist[1:])
            else:
                id = 'all'
            args = arglist[0]
            
        f = getattr(self, 'handle_%s_%s' %
                    (self.state, cmd), None)            
        if f:
            # Handler resolved with state and cmd 
            f(args, id)
        else:
            f = getattr(self, 'handle_%s' %
                (cmd), None)
            if f:
                # Handler resolved with only cmd
                f(args, id)
            else:
                self.sendLine("BAD")
                self.state = 'init'
                self.reset_work_vars()
    
    # Copied from twisted.mail.imap4
    def rawDataReceived(self, data):
        passon = self._pendingLiteral.write(data)
        if passon is not None:
            self.setLineMode(passon) # should I reset the state here?
    
    def reset_work_vars(self):
        self.work_vars = {}
    
    def _reset(self):
        self.work_vars = {}
        self.state = 'init'
    
    def parseID(self, idList):
        if len(idList) is 0:
            return 'all'
        else:
            try:
                return map(int, idList)
            except:
                return 'all'
    
    #####   
    ##### The PUSH command
    #####
    
    def handle_init_PUSH(self, args, id):
        
        # Parse the args
        if not args:
            self.push_finish("FAIL")
            return
        else:
            args_str = args

        self.work_vars['push_name'] = args_str
        self.work_vars['push_id'] = id
        # Setup to process the command
        self.state = 'pushing'
    
    def setup_literal(self, size):
        """Called by data command handlers."""
        d = defer.Deferred()
        self._pendingLiteral = LiteralString(size, d)
        self.setRawMode()
        return d        
    
    def push_finish(self,msg):
        self.sendLine("PUSH %s" % msg)
        self._reset()
    
    def handle_pushing_PICKLE(self, size_str, id):
        try:
            size = int(size_str)
        except (ValueError, TypeError):
            self.push_finish("FAIL")
        else:         
            d = self.setup_literal(size)
            d.addCallback(self.put_pickle)
    
    def put_pickle(self, package):
        try:
            data = pickle.loads(package)
        except pickle.PickleError:
            self.push_finish("FAIL")
        else:
            # What if this fails?  When could it?
            self.factory.pushPickle(self.work_vars['push_name'],
                package, self.work_vars['push_id'])
            self.push_finish("OK")
    
    #####   
    ##### The UPDATE command
    #####
    
    def handle_init_UPDATE(self, args, id):
        
        # Parse the args
        if not args:
            self.update_finish("FAIL")
            return
        else:
            args_str = args

        self.work_vars['update_dict'] = args_str
        self.work_vars['push_id'] = id
        # Setup to process the command
        self.state = 'updating'
    
    def setup_literal(self, size):
        """Called by data command handlers."""
        d = defer.Deferred()
        self._pendingLiteral = LiteralString(size, d)
        self.setRawMode()
        return d        
    
    def update_finish(self,msg):
        self.sendLine("UPDATE %s" % msg)
        self._reset()
    
    def handle_updating_PICKLE(self, size_str, id):
        try:
            size = int(size_str)
        except (ValueError, TypeError):
            self.update_finish("FAIL")
        else:         
            d = self.setup_literal(size)
            d.addCallback(self.update_pickle)
    
    def update_pickle(self, package):
        try:
            data = pickle.loads(package)
        except pickle.PickleError:
            self.update_finish("FAIL")
        else:
            # What if this fails?  When could it?
            self.factory.updatePickle(self.work_vars['update_name'],
                package, self.work_vars['update_id'])
            self.update_finish("OK")
    
    #####
    ##### The PULL command
    #####
    
    def handle_init_PULL(self, args, id):
        
        # Parse the args
        if not args:
            self.pull_finish("FAIL")
            return
        else:
            pull_name = args
            
        self.work_vars['pull_type'] = 'PICKLE'
        d = self.factory.pullPickle(pull_name, id)
                
        d.addCallback(self.pull_ok)
        d.addErrback(self.pull_fail)
    
    def pull_ok(self, resultList):
        # Add error code here and chain the callbacks
        try:
            result = map(pickle.loads,resultList)
            presult = pickle.dumps(result, 2)
        except pickle.PickleError:
            self.pull_finish("FAIL")
        else:
            self.sendLine("PICKLE %s" % len(presult))
            self.transport.write(presult)
            self.pull_finish("OK")
    
    def pull_fail(self, failure):
        self.pull_finish("FAIL")
    
    def pull_finish(self, msg):
        self.sendLine("PULL %s" % msg)
        self._reset()
    
    #####
    ##### The EXECUTE command
    #####
    
    def handle_init_EXECUTE(self, args, id):
        """Handle the EXECUTE command."""
                
        # Parse the args
        if not args:
            self.execute_finish("FAIL")
            return
            
        if "BLOCK" in args:
            block = True
            execute_cmd = args[6:]
        else:
            block = False
            execute_cmd = args
        
        if not execute_cmd:
            self.execute_finish("FAIL")
            return
        
        d = self.factory.execute(execute_cmd, id)
        d.addErrback(self.execute_fail)
        if block:
            d.addCallback(self.execute_ok_block)
        else:                   
            self.execute_finish("OK")   
            d.addCallback(self.execute_ok)
        return d
    
    def execute_ok(self, result):
        for tonotify in self.factory.notifiers():
            reactor.listenUDP(0,ResultReporterProtocol(result, tonotify) )
    
    def execute_ok_block(self, result):
        try:
            package = pickle.dumps(result, 2)
        except pickle.PickleError:
            self.execute_finish("FAIL")
        else:
            self.sendLine("PICKLE %i" % len(package))
            self.transport.write(package)
            self.execute_finish("OK")
            self.execute_ok(result)
    
    def execute_fail(self, f):
        self.execute_finish("FAIL")
    
    def execute_finish(self, msg):
        self.sendLine("EXECUTE %s" % msg)
        self._reset()
    
    #####
    ##### GETCOMMAND command
    #####
    
    def handle_init_GETCOMMAND(self, args, id):
        
        try: 
            index = int(args)
        except:
            index = None
        d = self.factory.getCommand(index, id)
        d.addCallbacks(self.getCommand_ok, self.getCommand_fail)
    
    def getCommand_ok(self, result):
        try:
            package = pickle.dumps(result, 2)
        except pickle.PickleError:
            self.getCommand_finish("FAIL")
        else:
            self.sendLine("PICKLE %i" % len(package))
            self.transport.write(package)
            self.getCommand_finish("OK")
    
    def getCommand_fail(self, f):
        self.getCommand_finish("FAIL")
    
    def getCommand_finish(self, msg):
        self.sendLine("GETCOMMAND %s" %msg)
    
    
    #####
    ##### GETLASTCOMMANDINDEX command
    #####
    
    def handle_init_GETLASTCOMMANDINDEX(self, args, id):
        
        d = self.factory.getLastCommandIndex(id)
        d.addCallbacks(self.getLastCommandIndex_ok, self.getLastCommandIndex_fail)
    
    def getLastCommandIndex_ok(self, result):
        try:
            package = pickle.dumps(result, 2)
        except pickle.PickleError:
            self.getLastCommandIndex_finish("FAIL")
        else:
            self.sendLine("PICKLE %i" % len(package))
            self.transport.write(package)
            self.getLastCommandIndex_finish("OK")
    
    def getLastCommandIndex_fail(self, f):
        self.getLastCommandIndex_finish("FAIL")
    
    def getLastCommandIndex_finish(self, msg):
        self.sendLine("GETLASTCOMMANDINDEX %s" %msg)
    
    #####
    ##### Kernel control commands
    #####
    
    def handle_init_STATUS(self, args, id):
        
        result = self.factory.status(id)
                
        try:
            package = pickle.dumps(result, 2)
        except pickle.PickleError:
            self.sendLine('STATUS FAIL')
        else:
            self.sendLine("PICKLE %s" % len(package))
            self.transport.write(package)
            self.sendLine('STATUS OK')
    
    def handle_init_NOTIFY(self, args, id):
        args_split = args.split(" ")
        if len(args_split) == 3:
            action, host, port = args_split
            try:
                port = int(port)
            except (ValueError, TypeError):
                self.sendLine("NOTIFY FAIL")
            else:
                if action == "TRUE":
                    self.factory.add_notifier((host, port))
                    self.sendLine('NOTIFY OK')
                elif action == "FALSE":
                    self.factory.del_notifier((host, port))
                    self.sendLine('NOTIFY OK')
                else:
                    self.sendLine('NOTIFY FAIL')
        else:
            self.sendLine('NOTIFY FAIL')
    
    # The RESET, KILL and DISCONNECT commands
    
    def handle_RESET(self, args, id):
        log.msg("Resettng engine %s" %id)
        self.factory.reset(id)
        self.sendLine('RESET OK')
        self._reset()
    
    def handle_KILL(self, args, id):
        log.msg("Killing engine %s" %id)
        self.factory.kill(id)
    
    def handle_DISCONNECT(self, args, id):
        log.msg("Disconnecting client...")
        self.sendLine("DISCONNECT OK")
        self.transport.loseConnection()
    

class IControlFactory(Interface):
    """interface to clients for controller"""
    
    #IQueuedEngine multiplexer methods
    def cleanQueue(self, id='all'):
        """Cleans out pending commands in an engine's queue."""
    
    #IEngine multiplexer methods
    def execute(self, lines, id='all'):
        """Execute lines of Python code."""
    
    def push(self, key, value, id='all'):
        """Put value into locals namespace with name key."""
    
    def pushPickle(self, key, package, id='all'):
        """Unpickle package and put into the locals namespace with name key."""
    
    def pull(self, key, id='all'):
        """Gets an item out of the self.locals dict by key."""
    
    def pullPickle(self, key, id='all'):
        """Gets an item out of the self.locals dist by key and pickles it."""
    
    def update(self, dictOfData, id='all'):
        """Updates the self.locals dict with the dictOfData."""
    
    def updatePickle(self, dictPickle, id='all'):
        """Updates the self.locals dict with the pickled dict."""
    
    def status(self, id='all'):
        """status of engines"""
    
    def reset(self, id='all'):
        """Reset the InteractiveShell."""
    
    def kill(self, id='all'):
        """kill engines"""
    
    def getCommand(self, i=None, id='all'):
        """Get the stdin/stdout/stderr of command i."""
    
    def getLastCommandIndex(self, id='all'):
        """Get the index of the last command."""
    


class ControlFactoryFromService(protocol.ServerFactory):
    """the controller factory"""
    
    implements(IControlFactory)
    
    protocol = ControlTCPProtocol
    
    def __init__(self, service):
        self.service = service
        self.notifiers = list
    
    #IQueuedEngine multiplexer methods
    def cleanQueue(self, id='all'):
        """Cleans out pending commands in an engine's queue."""
        return self.service.cleanQueue(id)
    
    #IEngine multiplexer methods
    def execute(self, lines, id='all'):
        """Execute lines of Python code."""
        return self.service.execute(lines, id)
    
    def push(self, key, value, id='all'):
        """Put value into locals namespace with name key."""
        return self.service.put(key, value, id)
    
    def pushPickle(self, key, value, id='all'):
        """Put value into locals namespace with name key."""
        return self.service.putPickle(key, value, id)
    
    def pull(self, key, id='all'):
        """Gets an item out of the self.locals dict by key."""
        return self.service.get(key, id)
    
    def pullPickle(self, key, id='all'):
        """Gets an item out of the self.locals dict by key."""
        return self.service.getPickle(key, id)
    
    def update(self, dictOfData, id='all'):
        """Updates the self.locals dict with the dictOfData."""
        return self.service.update(dictOfData, id)
    
    def updatePickle(self, dictOfData, id='all'):
        """Updates the self.locals dict with the dictOfData."""
        return self.service.updatePickle(dictOfData, id)
    
    def status(self, id='all'):
        """status of engines"""
        return self.service.status(id)
    
    def reset(self, id='all'):
        """Reset the InteractiveShell."""
        return self.service.reset(id)
    
    def kill(self, id='all'):
        """kill an engine"""
        return self.service.kill(id)
    
    def getCommand(self, i=None, id='all'):
        """Get the stdin/stdout/stderr of command i."""
        return self.service.getCommand(i, id)
    
    def getLastCommandIndex(self, id='all'):
        """Get the index of the last command."""
        return self.service.getLastCommandIndex(id)
    


components.registerAdapter(ControlFactoryFromService,
                        controllerservice.ControllerService,
                        IControlFactory)
