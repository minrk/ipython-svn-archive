import enthought.traits.api as traits

# For interactive testing
import tconfig; reload(tconfig)

from tconfig import TConfig, ConfigManager, ReadOnlyTConfig


class IpythonConfig(TConfig):

    m = traits.Int

    class InitOnly(TConfig, ReadOnlyTConfig):
        n = traits.Int
        x = traits.Float

    class Protocol(TConfig):
        ptype = traits.Str

        class Handler(TConfig):
            key = traits.Str

    class Machine(TConfig):
        ip = traits.Str
        port = traits.Int
