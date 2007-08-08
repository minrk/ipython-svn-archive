#!/usr/bin/env python
"""Install routine for the SnakeOil package.
"""

############ Nothing to configure below, unless you know what you're doing

# Stdlib modules
import os
import sys
from glob import glob

# A few handy globals
isfile = os.path.isfile
pjoin = os.path.join

# BEFORE importing distutils, remove MANIFEST. distutils doesn't properly
# update it when the contents of directories change.
if os.path.exists('MANIFEST'): os.remove('MANIFEST')

from distutils.core import setup

#### Code begins

# A little utility we'll need below, since glob() does NOT allow you to do
# exclusion on multiple endings!
def file_doesnt_endwith(test,endings):
    """Return true if test is a file and its name does NOT end with any
    of the strings listed in endings."""
    if not isfile(test):
        return False
    for e in endings:
        if test.endswith(e):
            return False
    return True

# Command-line scripts
script_files = filter(isfile, ['scripts/mkdoctest','scripts/py2doctest',
                               'scripts/oiltest','scripts/oilscript'])

# Documentation
exclude     = ('~','.pyc')
doc_exc = lambda f: file_doesnt_endwith(f,exclude)
doc_spec = [('doc',filter(doc_exc,glob('doc/*'))),
            ('doc/example',filter(doc_exc,glob('doc/example/*'))),
            ]

# All data files
data_files = doc_spec

# Release.py contains version, authors, license, url, keywords, etc.
execfile(os.path.join('snakeoil','release.py'))

# Call the setup() routine which does most of the work
setup(name             = name,
      version          = version,
      description      = description,
      long_description = long_description,
      author           = authors['Fernando'][0],
      author_email     = authors['Fernando'][1],
      url              = url,
      download_url     = download_url,
      license          = license,
      platforms        = platforms,
      keywords         = keywords,
      packages         = ['snakeoil'],
      scripts          = script_files,
      data_files       = data_files,
      )
