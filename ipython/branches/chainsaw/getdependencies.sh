#!/bin/bash

# This script attemps to use svn and wget or curl to download (not install) the direct
# dependencies of the IPython Kernel.  This packages are put into the parent directory.

cd ..
echo "Working in $PWD"

echo "Getting IPython..."
svn co http://ipython.scipy.org/svn/ipython/ipython/trunk ipython

echo "Getting Twisted..."
svn co svn://svn.twistedmatrix.com/svn/Twisted/trunk Twisted

echo "Getting Nevow"
svn co http://divmod.org/svn/Divmod/trunk/Nevow Nevow

echo "Getting ZopeInterface..."
if wget http://www.zope.org/Products/ZopeInterface/3.1.0c1/ZopeInterface-3.1.0c1.tgz; then
    echo "Using wget"
    tar -xvzf ZopeInterface-3.1.0c1.tgz
    rm ZopeInterface-3.1.0c1.tgz
elif curl http://www.zope.org/Products/ZopeInterface/3.1.0c1/ZopeInterface-3.1.0c1.tgz > ZopeInterface-3.1.0c1.tgz; then
    echo "Using curl"
    tar -xvzf ZopeInterface-3.1.0c1.tgz
    rm ZopeInterface-3.1.0c1.tgz
fi

echo "The IPython Kernel dependencies should now be in the parent directory."
echo "If they are not, you probably don't have svn and wget or curl installed."
echo "Please see the INSTALL file for further installation instructions."