#!/usr/bin/env python
"""Small script to clean up generated files.
"""
import os
import glob
import shutil

goodfiles = []
for ext in ['pybk', 'xml', 'py', 'png', 'orig']:
    goodfiles.extend(glob.glob('*.' + ext))
allfiles = glob.glob('*')
badfiles = sorted(set(allfiles) - set(goodfiles))

print 'Files being removed:'
for fn in badfiles:
    if os.path.isdir(fn):
        print '  %s/' % fn
    else:
        print '  %s' % fn
print
if raw_input('Do you want to delete them? [y/N] ').lower().startswith('y'):
    for fn in badfiles:
        if os.path.isdir(fn):
            shutil.rmtree(fn)
        else:
            os.unlink(fn)
