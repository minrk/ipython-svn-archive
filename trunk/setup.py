#!/usr/bin/env python
"""Setup script for IPython.

Under Posix environments it works like a typical setup.py script. Under
windows, only the install option is supported (sys.argv is reset to it),
because options like sdist require other utilities not available under
Windows."""

#*****************************************************************************
#       Copyright (C) 2001 Fernando Perez. <fperez@colorado.edu>
#
#  Distributed under the terms of the GNU Lesser General Public License (LGPL)
#
#    This code is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.
#
#  The full text of the LGPL is available at:
#
#                  http://www.gnu.org/copyleft/lesser.html
#*****************************************************************************

import sys,os
from glob import glob
from setupext import install_data_ext
isfile = os.path.isfile

# BEFORE importing distutils, remove MANIFEST. distutils doesn't properly
# update it when the contents of directories change.
if os.path.exists('MANIFEST'): os.remove('MANIFEST')

if os.name == 'posix':
    os_name = 'posix'
elif os.name in ['nt','dos']:
    os_name = 'windows'
else:
    print 'Unsupported operating system:',os.name
    sys.exit()

# Under Windows only 'install' is supported anyway, since 'sdist' requires
# lyxport (hence lyx,perl,latex,pdflatex,latex2html,sh,...)
if os_name == 'windows':
    setup = os.path.join(os.getcwd(),'setup.py')
    sys.argv = [setup,'install']

from distutils.core import setup

# update the manuals when building a source dist
if len(sys.argv) >= 2 and sys.argv[1] == 'sdist':
    from IPython.genutils import target_update
    # list of things to be updated. Each entry is a triplet of args for
    # target_update()
    to_update = [('doc/magic.tex',
                  ['IPython/Magic.py'],
                  "cd doc && ./update_magic.sh" ),
                 
                 ('doc/manual.lyx',
                  ['IPython/Release.py','doc/manual_base.lyx'],
                  "cd doc && ./update_version.sh" ),
                 
                 ('doc/manual/manual.html',
                  ['doc/manual.lyx',
                   'doc/magic.tex',
                   'doc/examples/example-gnuplot.py',
                   'doc/examples/example-magic.py',
                   'doc/examples/example-embed.py',
                   'doc/examples/example-embed-short.py',
                   'IPython/UserConfig/ipythonrc',
                   ],
                  "cd doc && "
                  "lyxport -tt --leave --pdf "
                  "--html -o '-noinfo -split +1 -local_icons' manual.lyx"),
                 
                 ('doc/new_design.pdf',
                  ['doc/new_design.lyx'],
                  "cd doc && lyxport -tt --pdf new_design.lyx")
                 ]
    for target in to_update:
        target_update(*target)

# Release.py contains version, authors, license, url, keywords, etc.
execfile(os.path.join('IPython','Release.py'))

# I can't find how to make distutils create a nested dir. structure, so
# in the meantime do it manually. Butt ugly.
docdirbase  = 'share/doc/IPython'
manpagebase = 'share/man/man1'
docfiles    = filter(isfile, glob('doc/*[!~|.lyx|.sh|.1|.1.gz]'))
examfiles   = filter(isfile, glob('doc/examples/*.py'))
manfiles    = filter(isfile, glob('doc/manual/*.html')) + \
              filter(isfile, glob('doc/manual/*.css'))
manpages    = filter(isfile, glob('doc/*.1.gz'))
cfgfiles    = filter(isfile, glob('IPython/UserConfig/*'))
scriptfiles = filter(isfile, glob('scripts/*'))

# Call the setup() routine which does most of the work
setup(name             = name,
      version          = version,
      description      = description,
      long_description = long_description,
      author           = authors['Fernando'][0],
      author_email     = authors['Fernando'][1],
      url              = url,
      license          = license,
      platforms        = platforms,
      keywords         = keywords,
      packages         = ['IPython', 'IPython.Extensions'],
      scripts          = scriptfiles,
      cmdclass         = {'install_data': install_data_ext},
      data_files       = [('data', docdirbase, docfiles),
                          ('data', os.path.join(docdirbase, 'examples'),
                           examfiles),
                          ('data', os.path.join(docdirbase, 'manual'),
                           manfiles),
                          ('data', manpagebase, manpages),
                          ('lib', 'IPython/UserConfig', cfgfiles)]
      )

# For Unix users, things end here.
# Under Windows, do some extra stuff.
if os_name=='windows':
    import ipython_win_post_install
    ipython_win_post_install.run(wait=1)
