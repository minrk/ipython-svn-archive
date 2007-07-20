import enthought.traits.api as traits

# import/reload base modules for interactive testing/development
import tconfig; reload(tconfig)

from tconfig import TConfig, ConfigManager, ReadOnlyTConfig, mkConfigObj


standard_color = traits.Trait ('black',
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
    backend = traits.Trait('TkAgg','WXAgg','GTKAgg','QtAgg','Qt4Agg')
    interactive = traits.Bool(True)
    
    class InitOnly(TConfig, ReadOnlyTConfig):
        """Things that can only be set at init time"""
        numerix = traits.Str('numpy')

    class lines(TConfig):
        linewidth = traits.Float(2.0)
        linestyle = traits.Trait('-','=','^')

    class figure(TConfig):
        figsize = traits.ListFloat([6.4,4.8])  # figure size in inches
        dpi = traits.Int(100)            # figure dots per inch
        facecolor = traits.Float(0.75)    # figure facecolor; 0.75 is scalar gray
        edgecolor = traits.Trait('white',standard_color)

        class subplot(TConfig):
            """The figure subplot parameters.  All dimensions are fraction
            of the figure width or height"""
            left = traits.Float(0.125)
            right = traits.Float(0.9)
            bottom = traits.Float(0.1)
            top = traits.Float(0.9)
