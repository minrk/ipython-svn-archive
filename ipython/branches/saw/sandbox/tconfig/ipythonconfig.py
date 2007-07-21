import enthought.traits.api as T

# For interactive testing
import tconfig; reload(tconfig)
from tconfig import TConfig, ReadOnlyTConfig


class IPythonconfig(TConfig):

    m = T.Int

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
