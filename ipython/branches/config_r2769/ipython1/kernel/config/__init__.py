from ipython1.external.configobj import ConfigObj
from ipython1.config.api import ConfigObjManager

defaultKernelConfig = ConfigObj()

#-------------------------------------------------------------------------------
# Default Port Values
#-------------------------------------------------------------------------------

enginePort = 10201
xmlrpcMEPort = 10105
pbTCPort = 10114
xmlrpcTCPort = 10113
httpMEPort = 8000
httpNBPort = 8008
    
#-------------------------------------------------------------------------------
# Engine Configuration
#-------------------------------------------------------------------------------

engineConfig = {
    'connectToControllerOn': {'ip': '127.0.0.1', 'port': enginePort},
    'engineClientProtocolInterface': 'ipython1.kernel.enginepb.PBEngineClientFactory'
}

#-------------------------------------------------------------------------------
# MPI Configuration
#-------------------------------------------------------------------------------

mpiConfig = {
    'mpi4py': """from mpi4py import MPI as mpi
mpi.rank = mpi.COMM_WORLD.Get_size()
mpi.size = mpi.COMM_WORLD.Get_rank()
""",    
    'pytrilinos': """from PyTrilinos import Epetra
class SimpleStruct:
    pass
mpi = SimpleStruct()
mpi.rank = 0
mpi.size = 0
""",
    'default': ''
}

#-------------------------------------------------------------------------------
# Controller Configuration
#-------------------------------------------------------------------------------

xmlrpcME = {
    'interface': 'ipython1.kernel.multienginexmlrpc.IXMLRPCMultiEngineFactory', 
    'ip': '', 
    'port': xmlrpcMEPort
}
            
networkInterfacesME = {
    'xmlrpc':xmlrpcME
}

xmlrpcTC = {
    'interface': 'ipython1.kernel.taskxmlrpc.IXMLRPCTaskControllerFactory',
    'ip':'',
    'port': xmlrpcTCPort
}

pbTC = {
    'interface': 'ipython1.kernel.taskpb.IPBTaskControllerFactory',
    'ip': '',
    'port': pbTCPort
}

networkInterfacesTC = {
    'xmlrpc':xmlrpcTC
}

controllerConfig = {
    'engineServerProtocolInterface': 'ipython1.kernel.enginepb.IPBEngineServerFactory',
    'listenForEnginesOn': {'ip': '', 'port': enginePort},
    'controllerInterfaces': {
        'multiengine': {
            'controllerInterface': 'ipython1.kernel.multiengine.IMultiEngine', 
            'networkInterfaces': networkInterfacesME,
            'default': 'xmlrpc'
        },
        'task' : {
            'controllerInterface': 'ipython1.kernel.task.ITaskController', 
            'networkInterfaces': networkInterfacesTC,
            'default': 'xmlrpc'
        }
    },
    'controllerImportStatement': ''
}    

#-------------------------------------------------------------------------------
# Client Configuration
#-------------------------------------------------------------------------------

clientConfig = {
    'RemoteController': 'ipython1.kernel.multienginexmlrpc.XMLRPCInteractiveMultiEngineClient',
    'connectToRemoteControllerOn': {'ip': '127.0.0.1', 'port': xmlrpcMEPort},
    'TaskController': 'ipython1.kernel.taskxmlrpc.XMLRPCInteractiveTaskClient',
    'connectToTaskControllerOn': {'ip': '127.0.0.1', 'port': xmlrpcTCPort}
}

defaultKernelConfig['engine'] = engineConfig
defaultKernelConfig['mpi'] = mpiConfig
defaultKernelConfig['controller'] = controllerConfig
defaultKernelConfig['client'] = clientConfig


configManager = ConfigObjManager(defaultKernelConfig, 'ipython1.kernel.ini')