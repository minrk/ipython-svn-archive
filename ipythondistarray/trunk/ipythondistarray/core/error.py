#----------------------------------------------------------------------------
# Exports
#----------------------------------------------------------------------------

__all__ = ['InvalidBaseCommError',
    'InvalidGridShapeError',
    'GridShapeError',
    'DistError',
    'DistMatrixError',
    'IncompatibleArrayError',
    'NullArrayError',
    'NullArrayAttributeError']

#----------------------------------------------------------------------------
# Exceptions
#----------------------------------------------------------------------------

class DistArrayError(Exception):
    pass

class InvalidBaseCommError(DistArrayError):
    pass

class InvalidGridShapeError(DistArrayError):
    pass

class GridShapeError(DistArrayError):
    pass

class DistError(DistArrayError):
    pass

class DistMatrixError(DistArrayError):
    pass

class IncompatibleArrayError(DistArrayError):
    pass

class NullCommunicatorError(DistArrayError):
    pass

class NullArrayError(DistArrayError):
    pass

class NullArrayAttributeError(NullArrayError):
    pass
