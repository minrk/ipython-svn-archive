from SocketServer import *
from esocket import *
import cPickle as pickle
import threading
import socket
import sys
import time

from Foundation import *

class EnhancedTCPServer(TCPServer):

    allow_reuse_address = True

    def __init__(self, server_address, RequestHandlerClass, 
        validator=None, advertiser=None):
        
        self.server_address = server_address
        self.RequestHandlerClass = RequestHandlerClass
        self.validator = validator
        self.advertiser = advertiser
        TCPServer.__init__(self, server_address, RequestHandlerClass)
    
    def verify_request(self, request, client_address):
        if not self.validator == None:
            return self.validator.validate(request, client_address)
        else:
            return True
                    
    def server_activate(self):
        print "Activating Server"
        TCPServer.server_activate(self)
        if not self.advertiser == None:
            result = self.advertiser.advertise(self.server_address)
            if not result:
                TCPServer.server_close(self)    
                raise Exception
                
    def server_close(self):
        self.advertiser.stopAdvertising()        
        TCPServer.server_close(self)    
        
# Connection Validator Classes

class BaseConnectionValidator(object):
    def __init__(self):
        """The ConnectionValidator class is used by both client and server
        to validate new connections.
        """
        pass
        
    def validate(self, request, client_address):
        """Validate the connection from socket sock.
        
        The EnhancedTCPServer calls this to verify a connection.
        This method should be overwritten in subclasses.  It should
        return True or False.
        """
        return True

class SimpleConnectionValidator(BaseConnectionValidator):
    """Validate a connection based on the peer IP address."""
    def __init__(self):
        self.allowed_ips = []
    
    def allow_ip(self, client_ip):
        """Register an IP address as allowed."""
        self.allowed_ips.append(socket.gethostbyname(client_ip))
    
    def validate(self, request, client_address):
        """See if client_address is an allowed IP."""
        print client_address
        if client_address[0] in self.allowed_ips:
            return True
        else:
            return False

# Base Service Advertiser and Browser

class BaseServiceAdvertiser(object):
    """A class used to advertise that a server is running."""
    
    def __init__(self):
        pass

    def advertise(self, server_address):
        """This is called by EnhancedTCPServer.server_activate() and 
        should be overwritten in subclasses.  Subclasses should call
        this to store the serviceAddress.
        
        Return True or False to indicate success.
        """
        self.serviceAddress = server_address
        return True
        
    def stopAdvertising(self):
        """Called by EnhancedTCPServer.server_close() to stop advertising
        the service.
        """
        pass
  
# Callback style service advertising
    
class CallbackServiceAdvertiser(BaseServiceAdvertiser):
    """Advertise by calling back a specific IP address."""
    
    def __init__(self, callbackAddress):
        """Create a service advertiser that will callback callbackAddress.
        
        Arguments:
        
        callbackAddress
            An (ip,port) tuple where a callbackServiceBrowser instance 
            is running.
        """
        self.callbackAddress = (socket.gethostbyname(callbackAddress[0]),
            callbackAddress[1])
        
    def advertise(self, server_address):
        """Callback the callbackAddress.
        
        Arguments:
        
        server_address
            The (ip,port) tuple where the service is running
        """
        self.serviceAddress = server_address
    
        # Try to callback the callbackAddress five times and then quit.
        tries = 0
        success = False
        while tries < 6 and not success:
            callbackSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                callbackSocket.connect(self.callbackAddress)
            except:
                tries += 1
                time.sleep(1)
            else:
                success = True
        
        # If we could connect to the callbackAddress, send info
        if success:
            if not callbackSocket.getpeername() == self.callbackAddress:
                callbackSocket.close()
                return False
            else:
                esock = Int32Socket(callbackSocket)
                esock.writeString(str(self.serviceAddress[1]))
                reply = esock.readString()
                callbackSocket.close()
                if reply=='ok':
                    return True
                else:
                    return False     
        else: # If the callback doesn't work then quit.
            return False

class CallbackServiceBrowser:
    """A class to collect information from callbackServiceAdvertisers.
    
    This class will browse for services calling it and store the (ip,port)
    tuples of the services that call it.
    """
    def __init__(self,addr,count):
        """Create browser to listen for services calling.
        
        Arguments:
        
        addr
            Address (ip, port) to listen on.
            
        count
            How many callers to listen for.
        """
    
        self.addr = addr        # The IP tuple to listen on
        self.count = count    # How many callers to wait for
        self._callers = []      # Who has called?
        self.callers_lock = threading.Lock()
        
    def browse(self,timeout = 10):
        """Starts the operator listening for callers."""
        
        # _watch can be called in the main thread if timeout > 0
        self._watch(self.addr,self.count,self.callers_lock,timeout)
        
        # Uncomment this code to run _watch in a 2nd thread.
        # This is useful if blocking sockets are being used.
        #self.t = threading.Thread(target=self._watch,args=[self.addr,self.count,self.callers_lock,timeout])
        #self.t.setDaemon(1)
        #self.t.start()

    def _watch(self,addr,count,callers_lock,timeout=10):
        """Watches for count callers.
        
        Notes:
        - Currently we are using sockets with timeouts.  This means
          that there could be fewer callers than count, which indicates
          a problem with one of the callers.
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.settimeout(timeout)
        s.bind(addr)
        s.listen(count)

        callers_lock.acquire()
        # Listen for count callers
        for caller in range(count-len(self._callers)):
            print "Looking for caller: ", caller
            try:
                caller_socket, caller_addr = s.accept()
            except:
                break
            else:
                caller_socket.settimeout(timeout) # prevents socket error
                es = Int32Socket(caller_socket)
                cip = caller_addr[0]
                cport = es.readString()
                es.writeString('ok')
                self._callers.append((cip,int(cport)))
                caller_socket.close()            
        s.close()
        callers_lock.release()  
        return
        
    def callers(self):
        """Returns the list of callers.  Thread safe."""
        self.callers_lock.acquire()
        clrs = self._callers
        self.callers_lock.release()
        return clrs

        
# Bonjour service classes

class BonjourServiceAdvertiser(BaseServiceAdvertiser):
    
    def __init__(self,serviceDomain,serviceType,serviceName):
        self.serviceDomain = serviceDomain
        self.serviceType = serviceType
        self.serviceName = serviceName
    
    def advertise(self, server_address):
        """Advertise using wide area Bonjour.
                
        Return True or False to indicate success.
        """
        self.serviceAddress = server_address
        
        self.ns = NSNetService.alloc().initWithDomain_type_name_port_(self.serviceDomain,
            self.serviceType, self.serviceName, self.serviceAddress[1])
        
        print "Publishing service with Bonjour"
            
        self.ns.publish()
        
        return True
        
    def stopAdvertising(self):
        """Called by EnhancedTCPServer.server_close() to stop advertising
        the service.
        """
        self.ns.stop()

    
        
class EchoRequestHandler(BaseRequestHandler):
    def handle(self):
        es = Int32Socket(self.request)
        data = es.readString()
        es.writeString(data)            
          
class BraidRequestHandler(BaseRequestHandler):

    def setup(self):
        self.action_handlers = {'PUSH':self.handle_push,
                        'PULL':self.handle_pull, 
                        'EXEC':self.handle_exec, 
                        'MOVE':self.handle_move,
                        'VALIDATEIP':self.handle_validateip, 
                        'FORWARDTO':self.handle_forwardto, 
                        'STATUS':self.handle_status, 
                        'RESET':self.handle_reset, 
                        'KILL':self.handle_kill}
        self.data_handler = BraidDataHandler(self.request)
        self.esock = Int32Socket(self.request)

    def handle(self):
        print "Handling..."
        connected = 1
        while connected:
        
        """If there is no string to read, since we're in a blocking socket, the 
        boss might sit there for an infinite amount of time.  Also, is the 
        string is corrupted or otherwise unreadable, the handler will have no 
        idea what to do.  We may, once again, get stuck in an infinite loop.  
        Additionally, since this is blocking, what happens to the worker if the 
        boss becomes disconnected somehow?
        """
        
            initial_action = self.esock.readString()
            print initial_action
            initial_action_list = initial_action.split(' ')
            if initial_action_list[0] == 'DISCONNECT':
                print "Disconnecting..."
                connected = 0
            else:
            
                """If the action identifier is corrupted or not present, there 
                is no disconnect possible and we get another infinite loop or 
                one very confused worker (probably both, actually).
                """
                
                print "Doing action..."
                handler = self.action_handlers.get(initial_action_list[0])
                if handler:
                    handler(initial_action_list[1:])
          
     # Handlers for different actions     
        
    def handle_push(self,args):
        print "Pushing...", args

        # Parse the args
        
        """If the boss forgets to put a name in, then part of the data is 
        considered to be the name by the worker and you get corrupted data.
        """
        
        name = args[0]
        forward = False
        """One of the computers that is supposed to be forwarded to is 
        unavailable, the computer that was trying to forward to it will not know 
        what to do (keep trying, don't forward, etc.).  If the forward doesn't 
        work, the worker should probably keep trying and report an error to the 
        boss.
        """
        
        if 'FORWARD' in args:
            forward = True
            
        # Read and unpack the data
        data = self.data_handler.read()

        # Queue the PUSH action
        print data
        
        # Forward if needed
        
        """Forwarding issue again.
        """
        
        if forward:
            print "Forwarding data..."
            
        # Reply to the boss
       
        """I guess it'll print "PUSH FAIL" if it doesn't work, so this will take
        care of the problem I identified above.
        """
        
        self.esock.writeString('PUSH OK')

    def handle_pull(self,args):
        
        """If the data you want pulled isn't there (or isn't identified by that 
        name) the worker has no idea what to do.
        """
        
        print "Pulling...", args
        name = args[0]
        if name == 'STDOUT':
            index = int(args[1])
            self.data_handler.write_stdout('this is stdout of cmd %i' % index)
            
            """If the stderr is a blank list, will the worker be able to deal 
            with that?  Also, how will the boss know that is has received the 
            error?  I guess this is addressed by the worker saying "PULL OK". 
            It would, however, be pretty funny if there were an error retrieving 
            the error.
            """
        elif name == 'STDERR':
            index = int(args[1])
            self.data_handler.write_stderr('this is stderr of cmd %i' % index)
        elif name == 'HISTORY':
            index = int(args[1])
            self.data_handler.write_history('this is history of cmd %i' % index)
        else:
            data = 10
            self.data_handler.write_pickle(data)
            
        self.esock.writeString('PULL OK')
        
            
    def handle_exec(self,args):
        
        """We may have a problem with the code we tell the worker to run.
        In which case, there would be an error.  Also, with everything we're 
        doing, we have to worry about data being corrupted en route.  We are
        using TCP and not UDP for send things like executable commands, but we
        could conceivably have corrupted data.
        """
        
        block = false
        forward = false
        
        print "Executing...", args
        """Get the pickled command and unpickle it so that it can be executed.
        """
        read_command = self.data_handler.read()

        #Execute the command
                     
        if BLOCK in args:
            block = True 
                          
        if FORWARD in args:
            forward = True
            print "Forwarding data..."
            self.handle_forwardto(args)
  
    
    def handle_move(self,args):
        print "Moving...", args
        return True        
    
    def handle_validateip(self,args):
        print "Validating IP...", args
        return True    
    
    def handle_forwardto(self,args):
        print "Forwarding to...", args
        return True    
    
    def handle_status(self, args):
        print "Status is...", args
        return True    
    
    def handle_reset(self, args):
        print "Resetting...", args
        return True    
    
    def handle_kill(self, args):
        print "Killing...", args
        return True
        
class BraidDataHandler:
    
    def __init__(self, sock):
        self.sock = sock
        self.esock = Int32Socket(self.sock)
        self.handlers = {'PICKLE':self.handle_pickle,
                         'ARRAY':self.handle_array,
                         'STDOUT':self.handle_stdout,
                         'STDERR':self.handle_stderr}
                         
    def read(self):
        data_type = self.esock.readString()
        handler = self.handlers.get(data_type)
        if handler:
            return handler()
        else:
            return None
            
    def handle_pickle(self):
        package = self.esock.readString()
        data = pickle.loads(package)
        return data
        
    def handle_array(self):
        return self.handle_pickle()
        
    def handle_stdout(self):
        return self.esock.readString()

    def handle_stderr(self):
        return self.esock.readString()
        
    def handle_history(self):
        return self.handle_pickle()
        
    def write_pickle(self, p):
        package = pickle.dumps(p,1)
        self.esock.writeString('PICKLE')
        self.esock.writeString(package)
        
    def write_array(self, a):
        package = pickle.dumps(a,2)
        self.esock.writeString('ARRAY')
        self.esock.writeString(package)
    
    def write_stdout(self, s):
        self.esock.writeString('STDOUT')
        self.esock.writeString(s)

    def write_stderr(self, s):
        self.esock.writeString('STDERR')
        self.esock.writeString(s)

    def write_history(self, h):
        package = pickle.dumps(h,1)
        self.esock.writeString('HISTORY')
        self.esock.writeString(package)
                  
if __name__ == '__main__':
          
    #advertiseAs = sys.argv[1]
            
    addr = ('',10104)
    validator = BaseConnectionValidator()
    #validator = SimpleConnectionValidator()
    #validator.allow_ip('cojo.scu.edu')
    advertiser = BaseServiceAdvertiser()
    #advertiser = CallbackServiceAdvertiser(('cojo.scu.edu',10001))
    #advertiser = BonjourServiceAdvertiser('bonjour.scu.edu',
    #    '_braid._tcp.',advertiseAs)
    
    server = EnhancedTCPServer(addr, BraidRequestHandler, validator, advertiser)
    server.serve_forever()