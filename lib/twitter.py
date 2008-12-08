#!/usr/bin/env python
"""
Twisted Twitter interface.

Copyright (c) 2008  Dustin Sallings <dustin@spy.net>
"""

import time
import base64
import urllib

from twisted.python import log
from twisted.internet import reactor
from twisted.web import client

import txml

SEARCH_URL="http://search.twitter.com/search.atom"

def __urlencode(h):
    rv = []
    for k,v in h.iteritems():
        rv.append('%s=%s' %
            (urllib.quote(k.encode("utf-8")), urllib.quote(v.encode("utf-8"))))
    return '&'.join(rv)

def search(query, delegate):
    "Perform a search query.  Get results in a deferred."
    return client.downloadPage(SEARCH_URL + '?' + __urlencode({'q': query}),
        txml.Feed(delegate))
