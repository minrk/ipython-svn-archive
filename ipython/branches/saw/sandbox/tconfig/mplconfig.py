import enthought.traits.api as T

# import/reload base modules for interactive testing/development
import tconfig; reload(tconfig)
from tconfig import TConfig, ReadOnlyTConfig

# Code begins

standard_color = T.Trait ('black',
                          {'black': (0.0, 0.0, 0.0, 1.0),
                           'blue': (0.0, 0.0, 1.0, 1.0),
                           'cyan': (0.0, 1.0, 1.0, 1.0),
                           'green': (0.0, 1.0, 0.0, 1.0),
                           'magenta': (1.0, 0.0, 1.0, 1.0),
                           'orange': (0.8, 0.196, 0.196, 1.0),
                           'purple': (0.69, 0.0, 1.0, 1.0),
                           'red': (1.0, 0.0, 0.0, 1.0),
                           'violet': (0.31, 0.184, 0.31, 1.0),
                           'yellow': (1.0, 1.0, 0.0, 1.0),
                           'white': (1.0, 1.0, 1.0, 1.0),
                           'transparent': (1.0, 1.0, 1.0, 0.0) } )

class MPLConfig(TConfig):

    # Valid backends, first is default
    backend = T.Trait('TkAgg','WXAgg','GTKAgg','QtAgg','Qt4Agg')
    interactive = T.Bool(True)
    
    class InitOnly(TConfig, ReadOnlyTConfig):
        """Things that can only be set at init time"""
        numerix = T.Str('numpy')

    class lines(TConfig):
        linewidth = T.Float(2.0)
        linestyle = T.Trait('-','=','^')

    class figure(TConfig):
        figsize = T.ListFloat([6.4,4.8])  # figure size in inches
        dpi = T.Int(100)            # figure dots per inch
        facecolor = T.Float(0.75)    # figure facecolor; 0.75 is scalar gray
        edgecolor = T.Trait('red',standard_color)

        class subplot(TConfig):
            """The figure subplot parameters.  All dimensions are fraction
            of the figure width or height"""
            left = T.Float(0.125)
            right = T.Float(0.9)
            bottom = T.Float(0.1)
            top = T.Float(0.9)
