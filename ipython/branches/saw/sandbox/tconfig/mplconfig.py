import enthought.traits.api as T
import os, pytz, tempfile
from matplotlib import colors as mcolors
from matplotlib import cbook

is_string_like = cbook.is_string_like

# import/reload base modules for interactive testing/development
import tconfig; reload(tconfig)
from tconfig import TConfig

# Code begins

def _is_writable_dir(p):
    """
    p is a string pointing to a putative writable dir -- return True p
    is such a string, else False
    """
    try: p + ''  # test is string like
    except TypeError: return False
    try:
        t = tempfile.TemporaryFile(dir=p)
        t.write('1')
        t.close()
    except OSError: return False
    else: return True

class IsWritableDir(T.TraitHandler):
    """
    """

    def validate(self, object, name, value):
        if _is_writable_dir(value):
            return value
        else:
            raise OSError('%s is not a writable directory'%value)

    def info(self):
        return "a writable directory"

def get_home():
    """Find user's home directory if possible.
    Otherwise raise error.

    :see:  http://mail.python.org/pipermail/python-list/2005-February/263921.html
    """
    path=''
    try:
        path=os.path.expanduser("~")
    except:
        pass
    if not os.path.isdir(path):
        for evar in ('HOME', 'USERPROFILE', 'TMP'):
            try:
                path = os.environ[evar]
                if os.path.isdir(path):
                    break
            except: pass
    if path:
        return path
    else:
        raise RuntimeError('please define environment variable $HOME')

def get_configdir():
    """
    Return the string representing the configuration dir.

    default is HOME/.matplotlib.  you can override this with the
    MPLCONFIGDIR environment variable
    """

    configdir = os.environ.get('MPLCONFIGDIR')
    if configdir is not None:
        if not _is_writable_dir(configdir):
            raise RuntimeError('Could not write to MPLCONFIGDIR="%s"'%configdir)
        return configdir

    h = get_home()
    p = os.path.join(get_home(), '.matplotlib')

    if os.path.exists(p):
        if not _is_writable_dir(p):
            raise RuntimeError("'%s' is not a writable dir; you must set %s/.matplotlib to be a writable dir.  You can also set environment variable MPLCONFIGDIR to any writable directory where you want matplotlib data stored "%h)
    else:
        if not _is_writable_dir(h):
            raise RuntimeError("Failed to create %s/.matplotlib; consider setting MPLCONFIGDIR to a writable directory for matplotlib configuration data"%h)

        os.mkdir(p)

    return p

backends = {'tkagg': 'TkAgg',
            'gtkagg': 'GTKAgg',
            'gtkcairo': 'GTKCairo',
            'qt4agg': 'Qt4Agg',
            'qtagg': 'QtAgg',
            'wxagg': 'WxAgg',
            'agg': 'Agg',
            'cairo': 'Cairo',
            'ps': 'PS',
            'pdf': 'PDF',
            'svg': 'SVG',
            'template': 'Templates' }

class BackendHandler(T.TraitHandler):
    """
    """

    def validate(self, object, name, value):
        try:
            return backends[value.lower()]
        except:
            return self.error(object, name, value)

    def info(self):
        be = backends.keys()
        be.sort
        return "one of %s"% ', '.join('%s'%i for i in be)

class BoolHandler(T.TraitHandler):
    """
    """

    bools = {'true': True,
             'yes': True,
             'y' : True,
             'on': True,
             1: True,
             True: True,
             'false': False,
             'no': False,
             'n': False,
             'off': False,
             0: False,
             False: False}
       
    def validate(self, object, name, value):
        try:
            return self.bools[value]
        except:
            return self.error(object, name, value)

    def info(self):
        return "one of %s"% ', '.join('%s'%i for i in self.bools.keys())

class ColorHandler(T.TraitHandler):
    """
    This is a clever little traits mechanism -- users can specify the
    color as any mpl color, and the traited object will keep the
    original color, but will add a new attribute with a '_' postfix
    which is the color rgba tuple.

    Eg

    class C(HasTraits):
        fillcolor = traits.Trait('black', ColorHandler())

    c = C()
    c.fillcolor = 'red'
    print c.fillcolor    # prints red
    print c.fillcolor_   # print (1,0,0,1)
    """
    is_mapped = True

    def post_setattr(self, object, name, value):
        object.__dict__[ name + '_' ] = self.mapped_value( value )

    def mapped_value(self, value ):
        if value is None: return None
        if is_string_like(value): value = value.lower()
        return mcolors.colorConverter.to_rgba(value)
       
    def validate(self, object, name, value):
        try:
            self.mapped_value(value)
        except ValueError:
            return self.error(object, name, value)
        else:            
            return value

    def info(self):
        return """\
any valid matplotlib color, eg an abbreviation like 'r' for red, a full
name like 'orange', a hex color like '#efefef', a grayscale intensity
like '0.5', or an RGBA tuple (1,0,0,1)"""


colormaps = ['Accent', 'Accent_r', 'Blues', 'Blues_r', 'BrBG', 'BrBG_r', 'BuGn',
             'BuGn_r', 'BuPu', 'BuPu_r', 'Dark2', 'Dark2_r', 'GnBu', 'GnBu_r', 
             'Greens', 'Greens_r', 'Greys', 'Greys_r', 'LUTSIZE', 'OrRd', 
             'OrRd_r', 'Oranges', 'Oranges_r', 'PRGn', 'PRGn_r', 'Paired', 
             'Paired_r', 'Pastel1', 'Pastel1_r', 'Pastel2', 'Pastel2_r', 'PiYG',
             'PiYG_r', 'PuBu', 'PuBuGn', 'PuBuGn_r', 'PuBu_r', 'PuOr', 'PuOr_r',
             'PuRd', 'PuRd_r', 'Purples', 'Purples_r', 'RdBu', 'RdBu_r', 'RdGy',
             'RdGy_r', 'RdPu', 'RdPu_r', 'RdYlBu', 'RdYlBu_r', 'RdYlGn', 
             'RdYlGn_r', 'Reds', 'Reds_r', 'Set1', 'Set1_r', 'Set2', 'Set2_r', 
             'Set3', 'Set3_r', 'Spectral', 'Spectral_r', 'YlGn', 'YlGnBu', 
             'YlGnBu_r', 'YlGn_r', 'YlOrBr', 'YlOrBr_r', 'YlOrRd', 'YlOrRd_r', 
             'autumn', 'autumn_r', 'binary', 'binary_r', 'bone', 'bone_r', 
             'cbook', 'cmapdat_r', 'cmapname', 'cmapname_r', 'cmapnames', 
             'colors', 'cool', 'cool_r', 'copper', 'copper_r', 'datad', 'flag', 
             'flag_r', 'gist_earth', 'gist_earth_r', 'gist_gray', 'gist_gray_r',
             'gist_heat', 'gist_heat_r', 'gist_ncar', 'gist_ncar_r', 
             'gist_rainbow', 'gist_rainbow_r', 'gist_stern', 'gist_stern_r', 
             'gist_yarg', 'gist_yarg_r', 'gray', 'gray_r', 'hot', 'hot_r', 
             'hsv', 'hsv_r', 'jet', 'jet_r', 'ma', 'mpl', 'pink', 'pink_r', 
             'prism', 'prism_r', 'revcmap', 'spectral', 'spectral_r', 'spring', 
             'spring_r', 'summer', 'summer_r', 'winter', 'winter_r']

class MPLConfig(TConfig):
    """
    This is a sample matplotlib configuration file.  It should be placed
    in HOME/.matplotlib/matplotlibrc (unix/linux like systems) and
    C:\Documents and Settings\yourname\.matplotlib (win32 systems)

    By default, the installer will overwrite the existing file in the
    install path, so if you want to preserve your's, please move it to
    your HOME dir and set the environment variable if necessary.

    This file is best viewed in a editor which supports ini or conf mode
    syntax highlighting

    Blank lines, or lines starting with a comment symbol, are ignored,
    as are trailing comments.  Other lines must have the format

      key = val   optional comment

    val should be valid python syntax, just as you would use when setting
    properties using rcParams. This should become more obvious by inspecting 
    the default values listed herein.

    Colors: for the color values below, you can either use
     - a matplotlib color string, such as r, k, or b
     - an rgb tuple, such as (1.0, 0.5, 0.0)
     - a hex string, such as #ff00ff or ff00ff
     - a scalar grayscale intensity such as 0.75
     - a legal html color name, eg red, blue, darkslategray

    ###CONFIGURATION BEGINS HERE
    see http://matplotlib.sourceforge.net/interactive.html
    """

    # Valid backends, first is default
    interactive = T.Trait(False, BoolHandler())
    toolbar = T.Trait('toolbar2', None)
    timezone = T.Trait('UTC', pytz.all_timezones)
    datapath = T.Trait(get_configdir(), IsWritableDir())
    numerix = T.Trait('numpy', 'numeric', 'numarray')
    maskedarray = T.false
    
    class backend(TConfig):
        """'GTKAgg', 'GTKCairo', 'QtAgg', 'Qt4Agg', 'TkAgg', 'Agg', 
        'Cairo', 'PS', 'PDF', 'SVG'"""
        use = T.Trait('TkAgg', BackendHandler())
        
        class cairo(TConfig):
            format = T.Trait('png', 'png', 'ps', 'pdf', 'svg')
        
        class tk(TConfig):
            """
            window_focus : Maintain shell focus for TkAgg
            pythoninspect: tk sets PYTHONINSPECT
            """

            window_focus = T.false
            pythoninspect = T.false
        
        class ps(TConfig):
            papersize = T.Trait('auto', 'letter', 'legal', 'ledger',
                                'A0', 'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7',
                                'A8', 'A9', 'A10',
                                'B0', 'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7',
                                'B8', 'B9', 'B10')
            useafm = T.false
            fonttype = T.Trait(3, 42)
            
            class distiller(TConfig):
                use = T.Trait(None, 'ghostscript', 'xpdf')
                resolution = T.Float(6000)
        
        class pdf(TConfig):
            compression = T.Range(0, 9, 6)
            fonttype = T.Trait(3, 42)
        
        class svg(TConfig):
            image_inline = T.true
            image_noscale = T.false
            embed_chars = T.false
    
    class lines(TConfig):
        linewidth = T.Float(1.0)
        linestyle = T.Trait('-','--','-.', ':', 'steps', '', ' ', None)
        color = T.Trait('blue',ColorHandler())
        solid_joinstyle = T.Trait('miter', 'round', 'bevel')
        solid_capstyle = T.Trait('butt', 'round', 'projecting')
        dash_joinstyle = T.Trait('miter', 'round', 'bevel')
        dash_capstyle = T.Trait('butt', 'round', 'projecting')
        marker = T.Trait(None, 'o', '.', ',', '^', 'v', '<', '>', 's', '+', 'x',
                         'D','d', '1', '2', '3', '4', 'h', 'H', 'p', '|', '_')
        markeredgewidth = T.Float(0.5)
        markersize = T.Float(6)
        antialiased = T.true

    class patch(TConfig):
        linewidth = T.Float(1.0)
        facecolor = T.Trait('blue',ColorHandler())
        edgecolor = T.Trait('black',ColorHandler())
        antialiased = T.true 

    class font(TConfig):
        family = T.Trait('sans-serif', 'serif', 'cursive', 'fantasy', 
                         'monospace')
        style = T.Trait('normal', 'italic', 'oblique')
        variant = T.Trait('normal', 'small-caps')
        weight = T.Trait('normal', 'bold', 'bolder', 'lighter',
                          100, 200, 300, 400, 500, 600, 700, 800, 900)
        stretch = T.Trait('ultra-condensed', 'extra-condensed', 'condensed',
                         'semi-condensed', 'normal', 'semi-expanded',
                         'expanded', 'extra-expanded', 'ultra-expanded',
                         'wider', 'narrower')
        size = T.Float(12.0)
        serif = T.ListStr(["Bitstream Vera Serif", "New Century Schoolbook", 
                 "Century Schoolbook L", "Utopia", "ITC Bookman", "Bookman", 
                 "Nimbus Roman No9 L", "Times New Roman", "Times", "Palatino", 
                 "Charter", "serif"])
        sans_serif = T.ListStr(["Bitstream Vera Sans", "Lucida Grande", "Verdana", 
                      "Geneva", "Lucid", "Arial", "Helvetica", "Avant Garde", 
                      "sans-serif"])
        cursive = T.ListStr(["Apple Chancery", "Textile", "Zapf Chancery", "Sand", 
                   "cursive"])
        fantasy = T.ListStr(["Comic Sans MS", "Chicago", "Charcoal", "Impact", "Western", 
                   "fantasy"])
        monospace = T.ListStr(["Bitstream Vera Sans Mono", "Andale Mono", "Nimbus Mono L",
                     "Courier New", "Courier", "Fixed", "Terminal", "monospace"])

    class text(TConfig):
        color = T.Trait('black',ColorHandler())
        usetex = T.false
        
        class latex(TConfig):
            unicode = T.false
            preamble = T.ListStr([])
            dvipnghack = T.false

    class axes(TConfig):
        hold = T.Trait(True, BoolHandler())
        facecolor = T.Trait('white',ColorHandler())
        edgecolor = T.Trait('black',ColorHandler())
        linewidth = T.Float(1.0)
        grid = T.Trait(True, BoolHandler())
        polargrid = T.Trait(True, BoolHandler())
        titlesize = T.Trait('large', 'xx-small', 'x-small', 'small', 'medium',
                            'large', 'x-large', 'xx-large', T.Float)
        labelsize = T.Trait('medium', 'xx-small', 'x-small', 'small', 'medium',
                            'large', 'x-large', 'xx-large', T.Float)
        labelcolor = T.Trait('black',ColorHandler())
        axisbelow = T.false
        
        class formatter(TConfig):
            limits = T.List(T.Float, [-7, 7], minlen=2, maxlen=2)
    
    class xticks(TConfig):
        color = T.Trait('black',ColorHandler())
        labelsize = T.Trait('small', 'xx-small', 'x-small', 'small', 'medium',
                            'large', 'x-large', 'xx-large', T.Float)
        direction = T.Trait('in', 'out')
        
        class major(TConfig):
            size = T.Float(4)
            pad = T.Float(4)

        class minor(TConfig):
            size = T.Float(2)
            pad = T.Float(4)

    class yticks(TConfig):
        color = T.Trait('black',ColorHandler())
        labelsize = T.Trait('small', 'xx-small', 'x-small', 'small', 'medium',
                            'large', 'x-large', 'xx-large', T.Float)
        direction = T.Trait('in', 'out')
        
        class major(TConfig):
            size = T.Float(4)
            pad = T.Float(4)

        class minor(TConfig):
            size = T.Float(2)
            pad = T.Float(4)

    class grid(TConfig):
        color = T.Trait('black',ColorHandler())
        linestyle = T.Trait('-','--','-.', ':', 'steps', '', ' ')
        linewidth = T.Float(0.5)

    class legend(TConfig):
        isaxes = T.true
        numpoints = T.Int(3)
        fontsize = T.Trait('medium', 'xx-small', 'x-small', 'small', 'medium',
                           'large', 'x-large', 'xx-large', T.Float)
        pad = T.Float(0.2)
        markerscale = T.Float(1.0)
        labelsep = T.Float(0.01)
        handlelen = T.Float(0.05)
        handletextsep = T.Float(0.02)
        axespad = T.Float(0.02)
        shadow = T.false

    class figure(TConfig):
        figsize = T.List(T.Float, [8,6], maxlen=2, minlen=2)
        dpi = T.Float(80)
        facecolor = T.Trait('0.75',ColorHandler())
        edgecolor = T.Trait('white',ColorHandler())

        class subplot(TConfig):
            """The figure subplot parameters.  All dimensions are fraction
            of the figure width or height"""
            left = T.Float(0.125)
            right = T.Float(0.9)
            bottom = T.Float(0.1)
            top = T.Float(0.9)
            wspace = T.Float(0.2)
            hspace = T.Float(0.2)

    class image(TConfig):
        aspect = T.Trait('equal', 'auto')
        interpolation = T.Trait('bilinear', 'nearest', 'bicubic', 'spline16', 
                                'spline36', 'hanning', 'hamming', 'hermite', 
                                'kaiser', 'quadric', 'catrom', 'gaussian', 
                                'bessel', 'mitchell', 'sinc', 'lanczos', 
                                'blackman')
        cmap = T.Trait('jet', *colormaps)
        lut = T.Int(256)
        origin = T.Trait('upper', 'lower')

    class contour(TConfig):
        negative_linestyle = T.Trait('dashed', 'solid')
    
    class savefig(TConfig):
        dpi = T.Float(100)
        facecolor = T.Trait('white',ColorHandler())
        edgecolor = T.Trait('white',ColorHandler())
    
    class verbose(TConfig):
        level = T.Trait('silent', 'helpful', 'debug', 'debug-annoying')
        fileo = T.Trait('sys.stdout', T.File)

if __name__ == "__main__":
    mplrc = MPLConfig()
    mplrc.backend.pdf.compression = 1.1
    print mplrc
