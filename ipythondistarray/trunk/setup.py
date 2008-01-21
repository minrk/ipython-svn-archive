
#--------- -------------------------------------------------------------------
# Metadata
#----------------------------------------------------------------------------

metadata = {
    'name'             : 'ipythondistarray',
    'version'          : '0.1',
    'description'      : 'Distributed Memory Arrays for Python',
    'keywords'         : 'parallel mpi distributed array',
    'license'          : 'New BSD',
    'author'           : 'Brian E. Granger',
    'author_email'     : 'ellisonbg@gmail.com',
    }

#----------------------------------------------------------------------------
# Extension modules
#----------------------------------------------------------------------------

def ext_modules():
    import sys
    
    maps = dict(name='ipythondistarray.maps',
                sources=['ipythondistarray/maps.c'])
    procgrid = dict(name='ipythondistarray.procgrid',
                    sources=['ipythondistarray/procgrid.c'])
    test_mpi = dict(name='ipythondistarray.tests.test_mpi',
                    sources=['ipythondistarray/tests/test_mpi.c'])
    allext = [maps, procgrid, test_mpi]
    return allext

def headers():
    # allheaders = ['mpi/ext/libmpi.h']
    return []

def executables():
    return []


#----------------------------------------------------------------------------
# Setup
#----------------------------------------------------------------------------

from distutils.core import setup
from mpidistutils import Distribution, Extension, Executable
from mpidistutils import config, build, build_ext
from mpidistutils import build_exe, install_exe, clean_exe

LibHeader = lambda header: str(header)
ExtModule = lambda extension: Extension(**extension)
ExeBinary = lambda executable: Executable(**executable)

def main():
    setup(packages = ['ipythondistarray',
                      'ipythondistarray.tests'],
          package_data = {'ipythondistarray' : ['include/*.pxi']},
          headers = [LibHeader(hdr) for hdr in headers()],
          ext_modules = [ExtModule(ext) for ext in ext_modules()],
          executables = [ExeBinary(exe) for exe in executables()],
          distclass = Distribution,
          cmdclass = {'config'      : config,
                      'build'       : build,
                      'build_ext'   : build_ext,
                      'build_exe'   : build_exe,
                      'clean_exe'   : clean_exe,
                      'install_exe' : install_exe,
                      },
          **metadata)

if __name__ == '__main__':
    # hack distutils.sysconfig to eliminate debug flags
    from distutils import sysconfig
    cvars = sysconfig.get_config_vars()
    cflags = cvars.get('OPT')
    if cflags:
        cflags = cflags.split()
        for flag in ('-g', '-g3'):
            if flag in cflags:
                cflags.remove(flag)
        cvars['OPT'] = str.join(' ', cflags)
    # and now call main
    main()
