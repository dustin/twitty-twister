#!/usr/bin/env python
"""
Twisted Twitter interface.

Copyright (c) 2008  Dustin Sallings <dustin@spy.net>
"""

import time
import base64
import urllib

from twisted.python import log
from twisted.internet import reactor, defer
from twisted.web import client

import txml

BASE_URL="http://twitter.com"
SEARCH_URL="http://search.twitter.com/search.atom"

def makeAuthHeader(username, password, headers=None):
    if not headers:
        headers = {}
    authorization = base64.encodestring('%s:%s' % (username, password))[:-1]
    headers['Authorization'] = "Basic %s" % authorization
    return headers

def __urlencode(h):
    rv = []
    for k,v in h.iteritems():
        rv.append('%s=%s' %
            (urllib.quote(k.encode("utf-8")), urllib.quote(v.encode("utf-8"))))
    return '&'.join(rv)

def __post(user, password, path, args={}):
    h = {'Content-Type': 'application/x-www-form-urlencoded'}
    return client.getPage((BASE_URL + "%s") % path, method='POST',
        postdata=__urlencode(args),
        headers=makeAuthHeader(user, password, h))

def verify_credentials(username, password):
    "Verify a user's credentials."
    return __post(username, password, "/account/verify_credentials.xml")

def __parsed_post(hdef, parser):
    deferred = defer.Deferred()
    hdef.addErrback(lambda e: deferred.errback(e))
    hdef.addCallback(lambda p: deferred.callback(parser(p)))
    return deferred

def update(username, password, status):
    "Update your status.  Returns the ID of the new post."
    return __parsed_post(__post(username, password, "/statuses/update.xml",
        {'status': status}), txml.parseUpdateResponse)

def search(query, delegate):
    "Perform a search query.  Get results in a deferred."
    return client.downloadPage(SEARCH_URL + '?' + __urlencode({'q': query}),
        txml.Feed(delegate))
