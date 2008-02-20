#!/usr/bin/env python
# encoding: utf-8

import sys
import os
import glob

def main():
    if not os.path.isdir('html'):
        os.mkdir('html')
    txt_files = glob.glob('*.txt')
    for f in txt_files:
        if f=='starthere.txt':
            html_file = 'index.html'
        else:
            html_file = os.path.splitext(f)[0]
        print "Converting to html: %s -> html/%s" % (f, html_file)
        cmd = 'rst2html.py %s html/%s' % (f, html_file)
        os.system(cmd)


if __name__ == '__main__':
    main()

