#!/usr/bin/env python
"""Setup script for IPython.

Under Posix environments it works like a typical setup.py script. Under
windows, only the install option is supported (sys.argv is reset to it),
because options like sdist require other utilities not available under
Windows."""

#*****************************************************************************
#       Copyright (C) 2001 Fernando Pérez. <fperez@pizero.colorado.edu>
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
                  "lyxport -tt --leave --pdf --html -o '-noinfo -split +1' "
                  "manual.lyx"),
                 
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
docfiles    = filter(os.path.isfile, glob('doc/*[!~|.lyx|.sh]'))
examfiles   = filter(os.path.isfile, glob('doc/examples/*.py'))
manfiles    = filter(os.path.isfile, glob('doc/manual/*.html')) + \
              filter(os.path.isfile, glob('doc/manual/*.css'))
cfgfiles    = filter(os.path.isfile, glob('IPython/UserConfig/*'))
scriptfiles = filter(os.path.isfile, glob('scripts/*'))

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
      data_files       = [('base', docdirbase, docfiles),
                          ('base', os.path.join(docdirbase, 'examples'),
                           examfiles),
                          ('base', os.path.join(docdirbase, 'manual'),
                           manfiles),
                          ('lib', 'IPython/UserConfig', cfgfiles)]
      )

# For Unix users, things end here.
# Under Windows, do some extra stuff.
if os_name == 'windows':
    try:
        import shutil,pythoncom
        from win32com.shell import shell
        import _winreg as wreg
    except ImportError:
        print """
You seem to be missing the PythonWin extensions necessary for automatic
installation.  You can get them (free) from
http://starship.python.net/crew/mhammond/

Please see the manual for details if you want to finish the installation by
hand, or get PythonWin and repeat the procedure.

Press <Enter> to exit this installer."""
        raw_input()
        sys.exit()

    #--------------------------------------------------------------------------
    def make_shortcut(fname,target,args='',start_in='',comment='',icon=None):
        """Make a Windows shortcut (.lnk) file.

        make_shortcut(fname,target,args='',start_in='',comment='',icon=None)

        Arguments:
            fname - name of the final shortcut file (include the .lnk)
            target - what the shortcut will point to
            args - additional arguments to pass to the target program
            start_in - directory where the target command will be called
            comment - for the popup tooltips
            icon - optional icon file. This must be a tuple of the type 
            (icon_file,index), where index is the index of the icon you want
            in the file. For single .ico files, index=0, but for icon libraries
            contained in a single file it can be >0.
        """

        shortcut = pythoncom.CoCreateInstance(
            shell.CLSID_ShellLink, None,
            pythoncom.CLSCTX_INPROC_SERVER, shell.IID_IShellLink
        )
        shortcut.SetPath(target)
        shortcut.SetArguments(args)
        shortcut.SetWorkingDirectory(start_in)
        shortcut.SetDescription(comment)
        if icon:
            shortcut.SetIconLocation(*icon)
        shortcut.QueryInterface(pythoncom.IID_IPersistFile).Save(fname,0)


    #--------------------------------------------------------------------------
    # 'Main' code

    # Find where the Start Menu and My Documents are on the filesystem
    key = wreg.OpenKey(wreg.HKEY_CURRENT_USER,
                       r'Software\Microsoft\Windows\CurrentVersion'
                       r'\Explorer\Shell Folders')

    start_menu_dir = wreg.QueryValueEx(key,'Programs')[0]
    my_documents_dir = wreg.QueryValueEx(key,'Personal')[0]
    key.Close()

    # Find where the 'program files' directory is
    key = wreg.OpenKey(wreg.HKEY_LOCAL_MACHINE,
                       r'SOFTWARE\Microsoft\Windows\CurrentVersion')

    program_files_dir = wreg.QueryValueEx(key,'ProgramFilesDir')[0]
    key.Close()

    # File and directory names
    ip_start_menu_dir = start_menu_dir + '\\IPython'
    ip_install_dir = program_files_dir + '\\IPython'  # Actual files
    doc_dir = ip_install_dir+'\\doc'
    ip_filename = ip_install_dir+'\\IPython_shell.py'
    pycon_icon = doc_dir+'\\pycon.ico'

    if not os.path.isdir(ip_install_dir):
        os.mkdir(ip_install_dir)

    # Copy startup script and documentation
    shutil.copy(sys.prefix+'\\Scripts\\ipython',ip_filename)
    if os.path.isdir(doc_dir):
        shutil.rmtree(doc_dir)
    shutil.copytree('doc',doc_dir)

    # make shortcuts for IPython, html and pdf docs.
    print '\n\n\nMaking entries for IPython in Start Menu...',

    # Create shortcuts in Programs\IPython:
    if not os.path.isdir(ip_start_menu_dir):
        os.mkdir(ip_start_menu_dir)
    os.chdir(ip_start_menu_dir)

    man_pdf = doc_dir + '\\manual.pdf'
    man_htm = doc_dir + '\\manual\\manual.html'

    make_shortcut('IPython.lnk',sys.executable, '"%s"' % ip_filename,
                  my_documents_dir,
                  'IPython - Enhanced python command line interpreter',
                  (pycon_icon,0))
    make_shortcut('Manual in HTML format.lnk',man_htm,'','',
                  'IPython Manual - HTML format')
    make_shortcut('Manual in PDF format.lnk',man_pdf,'','',
                  'IPython Manual - PDF format')

    print """Done.

I created the directory %(ip_install_dir)s. There you will find the
IPython startup script and manuals.

An IPython menu was also created in your Start Menu, with entries for
IPython itself and the manual in HTML and PDF formats.

For reading PDF documents you need the freely available Adobe Acrobat
Reader. If you don't have it, you can download it from:
http://www.adobe.com/products/acrobat/readstep2.html

Finished with IPython installation. Press Enter to exit this installer.""" % locals()
    raw_input()

def dummy(): pass  # Stupid fix for emacs' python mode. Don't remove.
