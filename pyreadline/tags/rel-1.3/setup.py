# -*- coding: utf-8 -*-

#*****************************************************************************
#       Copyright (C) 2003-2006 Gary Bishop.
#       Copyright (C) 2006  Jorgen Stenarson. <jorgen.stenarson@bostream.nu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

import glob,shutil,os
from distutils.core import setup
execfile('pyreadline/release.py')

# vivainio preferably no manual setup here...
#try:
#    os.chdir("doc")
#    execfile('update_manual.py')
#finally:
#os.chdir("..")

setup(name=name,
      version          = version,
      description      = description,
      long_description = long_description,
      author           = authors["Jorgen"][0],
      author_email     = authors["Jorgen"][1],
      maintainer       = authors["Jorgen"][0],
      maintainer_email = authors["Jorgen"][1],
      license          = license,
      classifiers      = classifiers,
      url              = url,
#      download_url     = download_url,
      platforms        = platforms,
      keywords         = keywords,
      py_modules       = ['readline'],
      packages         = ['pyreadline'],
      package_data     = {'pyreadline':['configuration/*']},
      data_files       = [('share/doc/pyreadline', glob.glob("doc/*.pdf")+glob.glob("doc/*.txt")),
                         ]
      )

