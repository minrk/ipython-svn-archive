"""Classes for using Apple's Bonjour with Twisted."""
import bonjour

from twisted.internet.interfaces import IReadDescriptor
from twisted.python import log
from twisted.internet import defer
from zope.interface import implements, classImplements

class BonjourError(Exception):
    """Bonjour Error"""
    
    def __init__(self, errorCode):
        self.errorCode = errorCode
    
    def __str__(self):
        return "Bonjour Error: %i" % self.errorCode
            
class BonjourRegistrationError(BonjourError):
    """Bonjour Registration Error"""
    
    def __str__(self):
        return "Bonjour Registration Error: %i" % self.errorCode    
            
class BonjourDescriptor(object,log.Logger):
    """Integrates a Bonjour file desc. into the Twisted event loop.
    
    The user should not create instances of this class directly.  They
    should instead be created by the higher level classes like
    BonjourAdvertiser, BonjourBrowser, etc."""

    implements(IReadDescriptor)
    
    def __init__(self, fd, sdRef):
        """Wrap a Bonjour file descriptor
        
        @arg fd: file Descriptor to wrap
        @type fd: int
        @arg sdRef: Initialized ServiceDiscovery reference
        """
        self.fd = fd
        self.sdRef = sdRef
        
    def fileno(self):
        """Return the raw file descriptor"""
        return self.fd
        
    def doRead(self):
        """Called by the Twited event loop when the fd is ready to read."""
        ret = bonjour.DNSServiceProcessResult(self.sdRef)
        
    def connectionLost(self, reason):
        """Called by the Twisted event loop when things are shutting down."""
        log.msg("Stopping Bonjour Advertisement")
        if self.sdRef is not None:
            bonjour.DNSServiceRefDeallocate(self.sdRef)
            self.sdRef = None
        
        
class BonjourAdvertiser(object):
    """Advertise a service using Bonjour."""
    
    def __init__(self, name, regtype, port, reactor,
                 flags=0, interfaceIndex=0, domain='local',host='', 
                 txtLen=0, txtRecord=None, context=None):
        """Create an object to advertise a Bonjour service.
        
        @arg name: The name of the service
        @type name: str
        @arg regtype: The type of service, like _http._tcp
        @type regtype: str
        @arg domain: The Bonjour domain to browse, like local
        @type domain: str
        @arg port: The port to advertise as
        @type port: int
        @arg reactor: The Twisted reactor
        """
        
        self.name = name
        self.regtype = regtype
        self.domain = domain
        self.port = port
        self.reactor = reactor
        self.flags = flags
        self.interfaceIndex = interfaceIndex
        self.host = host
        self.txtLen = txtLen
        self.txtRecord = txtRecord
        self.context = context
        
    def startAdvertising(self):
        """Advertise the service with Bonjour.
        
        This method returns a deferred.  Upon success, the result
        is a dictionary of information about the service.  Upon failure,
        the result is a Failure object that knows the BonjourError code.
        """
        
        # Allocate a Bonjour Service Reference
        self.sdRef = bonjour.AllocateDNSServiceRef()
        
        # Initiate Registration of the service
        ret = bonjour.pyDNSServiceRegister(self.sdRef,
            self.flags,
            self.interfaceIndex,
            self.name,
            self.regtype,
            self.domain,
            self.host,
            self.port,
            self.txtLen,
            self.txtRecord,
            self._registrationCallback,
            self.context)
                        
        # Error check for immediate failure
        if ret != bonjour.kDNSServiceErr_NoError:
            return defer.fail(BonjourRegistrationError(ret))
            
        # Get the file descriptor and integrate with twisted
        self.fd = bonjour.DNSServiceRefSockFD(self.sdRef)
        self.bonjourDesc = BonjourDescriptor(self.fd, self.sdRef)
        self.reactor.addReader(self.bonjourDesc)
        
        self.d = defer.Deferred()
        return self.d
        
    def stopAdvertising(self):
        """Stop advertising the service."""
        
        # Remove the Reader Deallocate the serviceReference
        self.reactor.removeReader(self.bonjourDesc)
        if self.sdRef is not None:
            bonjour.DNSServiceRefDeallocate(self.sdRef)
            self.sdRef = None

    def _registrationCallback(self,sdRef,flags,errorCode,name,
                             regtype,domain,context):
        """Callback function for Bonjour Registration.
        
        This callback fires the deferred with either a dictionary of 
        information about the service, or a Failure object.
        """
                             
        if errorCode != bonjour.kDNSServiceErr_NoError:
            self.d.errback(BonjourRegistrationError(errorCode))
        else:
            self.d.callback({'sdRef' : sdRef,
                             'flags': flags,
                             'name' : name,
                             'regtype' : regtype,
                             'domain' : domain,
                             'context' : context})

        
