#!/bin/bash

cd ..
echo "Working in $PWD"

echo "Getting Twisted..."
svn co svn://svn.twistedmatrix.com/svn/Twisted/trunk Twisted

echo "Getting Nevow"
svn co http://divmod.org/svn/Divmod/trunk/Nevow Nevow

echo "Getting ZopeInterface..."
if [ -e "wget" ] && [ -x "wget"]; then
    echo "Using wget"
    wget http://www.zope.org/Products/ZopeInterface/3.1.0c1/ZopeInterface-3.1.0c1.tgz
    tar -xvzf ZopeInterface-3.1.0c1.tgz
elif [ -e "curl" ] && [ -x "curl" ]; then
    echo "Using curl"
    wget http://www.zope.org/Products/ZopeInterface/3.1.0c1/ZopeInterface-3.1.0c1.tgz
    tar -xvzf ZopeInterface-3.1.0c1.tgz
fi
