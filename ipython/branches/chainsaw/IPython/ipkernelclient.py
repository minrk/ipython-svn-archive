from twisted.internet import reactor, protocol
from twisted.protocols import basic

class IPythonTCPClientProtocol(basic.Int23StringReceiver):
    pass

class IPythonTCPClientFactory(protocol.ClientFactory):
    pass
