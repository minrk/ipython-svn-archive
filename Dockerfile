FROM shimizukawa/python-all-dev:ubuntu-12.04

ENV PYTHON=python2.4
ADD wget.py /tmp/wget.py
RUN python3.4 /tmp/wget.py \
    https://pypi.python.org/packages/source/s/setuptools/setuptools-1.4.2.tar.gz \
 && tar -xzf setuptools-1.4.2.tar.gz \
 && cd setuptools-1.4.2 \
 && $PYTHON setup.py install \
 && cd .. \
 && rm -rf setuptools-*


RUN $PYTHON -m easy_install sqlalchemy==0.3.11 zope.interface==3.3.0 simplejson==1.9.2
# ADD supports bzip, image doesn't!
COPY deps/Twisted-2.5.0.tar.gz Twisted-2.5.0.tar.gz
RUN tar -xzf Twisted-2.5.0.tar.gz \
 && cd Twisted-2.5.0 \
 && $PYTHON setup.py install \
 && cd .. \
 && rm -rf Twisted-2.5.0

# nevow 0.9.10
# nevow 0.9.11 introduces id-rewriting breaking getElementById assumptions
# can't easy_instal since eggs don't work
RUN python3.4 /tmp/wget.py https://github.com/twisted/nevow/archive/6b89f5e69e195cf42cb9c0c8159b5b5206606b73.tar.gz nevow.tar.gz \
 && tar -xzf nevow.tar.gz \
 && cd nevow-* \
 && $PYTHON setup.py install \
 && cd .. \
 && rm -rf nevow.tar.gz nevow-*


COPY ipython/tags/rel-0.8.2 /src/ipython
RUN cd /src/ipython && $PYTHON setup.py install

COPY ipython/branches/chainsaw /src/ipython1
RUN cd /src/ipython1 && $PYTHON setup.py install

RUN mkdir /root/.ipython

EXPOSE 8080

ADD launch /usr/local/bin/launch
CMD ["launch"]
