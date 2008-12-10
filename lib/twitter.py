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

def __get(user, password, path, delegate, params={}):
    url = BASE_URL + path
    if params:
        url += '?' + __urlencode(params)
    return client.downloadPage(url, txml.Feed(delegate),
        headers=makeAuthHeader(user, password))

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

def friends(username, password, delegate, params={}):
    """Get updates from friends.

    See search for example of how results are returned."""
    return __get(username, password, "/statuses/friends_timeline.atom",
        delegate, params)

def user_timeline(username, password, delegate, user=None, params={}):
    """Get the most recent updates for a user.

    If no user is specified, the statuses for the authenticating user are
    returned.

    See search for example of how results are returned."""
    if user:
        params['id'] = user
    return __get(username, password, "/statuses/user_timeline.atom",
        delegate, params)

def direct_messages(username, password, delegate, params={}):
    """Get direct messages for the authenticating user.

    See search for example of how results are returned."""
    return __get(username, password, "/direct_messages.atom", delegate, params)

def replies(username, password, delegate, params={}):
    """Get the most recent replies for the authenticating user.

    See search for example of how results are returned."""
    return __get(username, password, "/statuses/replies.atom", delegate, params)

def follow(username, password, user):
    """Follow the given user.

    Returns no useful data."""
    return __post(username, password, '/friendships/create/%s.xml' % user)

def leave(username, password, user):
    """Stop following the given user.

    Returns no useful data."""
    return __post(username, password, '/friendships/destroy/%s.xml' % user)

def list_friends(username, password, delegate, user=None, params=None):
    """Get the list of friends for a user.

    Calls the delegate with each user object found."""
    if user:
        url = BASE_URL + '/statuses/friends/' + user + '.xml'
    else:
        url = BASE_URL + '/statuses/friends.xml'
    if params:
        url += '?' + __urlencode(params)
    return client.downloadPage(url, txml.Users(delegate),
        headers=makeAuthHeader(username, password))

def search(query, delegate, args=None):
    """Perform a search query.
    
    Results are given one at a time to the delegate.  An example delegate
    may look like this:
    
    def exampleDelegate(entry):
        print entry.title"""
    if args is None:
        args = {}
    args['q'] = query
    return client.downloadPage(SEARCH_URL + '?' + __urlencode(args),
        txml.Feed(delegate))
