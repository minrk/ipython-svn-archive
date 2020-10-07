FROM shimizukawa/python-all-dev:ubuntu-12.04

ENV PYTHON=python2.5
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

COPY ipython/tags/rel-0.8.2 /src/ipython
RUN cd /src/ipython && $PYTHON setup.py install

COPY ipython/branches/saw /src/ipython1
RUN cd /src/ipython1 && $PYTHON setup.py develop

RUN mkdir /root/.ipython

EXPOSE 8008

ADD launch /usr/local/bin/launch
CMD ["launch"]
