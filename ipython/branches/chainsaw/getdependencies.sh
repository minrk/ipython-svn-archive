#!/bin/bash

cd ..
echo "Working in $PWD"

echo "Getting Twisted..."
svn co svn://svn.twistedmatrix.com/svn/Twisted/trunk Twisted

echo "Getting Nevow"
svn co http://divmod.org/svn/Divmod/trunk/Nevow Nevow

echo "Getting ZopeInterface..."
if wget http://www.zope.org/Products/ZopeInterface/3.1.0c1/ZopeInterface-3.1.0c1.tgz; then
    echo "Using wget"
    tar -xvzf ZopeInterface-3.1.0c1.tgz
elif curl http://www.zope.org/Products/ZopeInterface/3.1.0c1/ZopeInterface-3.1.0c1.tgz; then
    echo "Using curl"
    tar -xvzf ZopeInterface-3.1.0c1.tgz
fi
