#!/usr/bin/env python3.4
"""Download a file"""
import sys
from urllib.parse import urlparse
from urllib.request import urlretrieve

src = sys.argv[1]
if len(sys.argv) >= 3:
    dest = sys.argv[2]
else:
    dest = urlparse(src).path.rsplit("/", 1)[-1]
urlretrieve(src, dest)
