#*****************************************************************************
#       Copyright (C) 2005 Robert Kern. All rights reserved.
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

class XMLNS(object):
    """Convenience object for handling namespaced tag names in ElementTree-like
    APIs.

    ElementTree-like APIs use an inconvenient syntax for representing tags
    within namespaces. E.g.

        rdf:RDF -> {http://www.w3.org/1999/02/22-rdf-syntax-ns#}RDF
        dc:creator -> {http://purl.org/dc/elements/1.1/}creator

    Instances of XMLNS use __getattr__ magic to generate tags with this syntax.
    You can also use __getitem__ for those tags which are not valid Python
    identifiers.

        rdf = XMLNS('rdf', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#')
        xsl = XMLNS('xsl', 'http://www.w3.org/1999/XSL/Transform')
        rdf.RDF == '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}RDF'
        xsl['value-of'] == '{http://www.w3.org/1999/XSL/Transform}value-of'

    Constructor:
        XMLNS(prefix, url)
    """
    def __init__(self, prefix, url):
        self._url = url
        self._qname_prefix = u'{%s}'%url
        self._prefix = prefix

    def __getitem__(self, tag):
        return self._qname_prefix + tag
    __getattr__ = __getitem__

def nsmap(*args):
    """Create a dictionary mapping prefixes to namespace URLs from XMLNS
    instances.
    """
    d = {}
    for ns in args:
        d[ns._prefix] = ns._url
    return d

def strip_ns(elems, *namespaces):
    """Remove namespaces from an iterable of elements.
    """
    for ns in namespaces:
        curly_prefix=ns._qname_prefix
        n = len(curly_prefix)
        for el in elems:
            if el.tag.startswith(curly_prefix):
                el.tag = el.tag[n:]

# These are standards
rdf = XMLNS('rdf', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#')
dc = XMLNS('dc', 'http://purl.org/dc/elements/1.1/')
xsl = XMLNS('xsl', 'http://www.w3.org/1999/XSL/Transform')
xlink = XMLNS('xlink', 'http://www.w3.org/1999/xlink')
db = XMLNS('db', 'http://docbook.org/ns/docbook')

# These are namespaces we've defined
ip = XMLNS('ip', 'http://ipython.scipy.org/notebook-xml')
iptest = XMLNS('iptest', 'http://ipython.scipy.org/notebook-test-xml')
