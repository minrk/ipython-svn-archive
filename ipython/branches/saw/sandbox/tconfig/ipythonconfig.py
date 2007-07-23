import enthought.traits.api as T

# For interactive testing
import tconfig; reload(tconfig)
from tconfig import TConfig, ReadOnlyTConfig


class IPythonConfig(TConfig):
    """Class Docstring

    More"""

    m = T.Int

    select = T.Trait('only','one','of','these')
    
    class InitOnly(TConfig, ReadOnlyTConfig):
        n = T.Int
        x = T.Float

    class Protocol(TConfig):
        include = T.Str
        ptype = T.Str

        class Handler(TConfig):
            key = T.Str

    class Machine(TConfig):
        ip = T.Str
        port = T.Int
