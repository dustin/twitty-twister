#!/usr/bin/env python
"""

Copyright (c) 2008  Dustin Sallings <dustin@spy.net>
"""

import os
import sys

sys.path.append(os.path.join(sys.path[0], '..', 'lib'))
sys.path.append('lib')

from twisted.internet import reactor, protocol, defer, task

import twitter

fetchCount = 0

@defer.deferredGenerator
def getSome(tw, user):
    global fetchCount
    fetchCount = 0

    def gotEntry(msg):
        global fetchCount
        fetchCount += 1
        assert msg.title.startswith(user + ": ")
        l = len(user)
        print msg.title[l+2:]

    page = 1
    while True:
        fetchCount = 0
        sys.stderr.write("Fetching page %d\n" % page)
        d = tw.user_timeline(gotEntry, user, {'count': '200', 'page': str(page)})
        page += 1
        wfd = defer.waitForDeferred(d)
        yield wfd
        wfd.getResult()

        if fetchCount == 0:
            reactor.stop()

user = None
if len(sys.argv) > 3:
    user = sys.argv[3]

tw = twitter.Twitter(sys.argv[1], sys.argv[2])

defer.maybeDeferred(getSome, tw, user)

reactor.run()
