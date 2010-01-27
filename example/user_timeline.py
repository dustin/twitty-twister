#!/usr/bin/env python
"""

Copyright (c) 2008  Dustin Sallings <dustin@spy.net>
"""

import os
import sys

from twisted.internet import reactor, protocol, defer, task

from twittytwister import twitter

fetchCount = 0

@defer.deferredGenerator
def getSome(tw, user):
    global fetchCount
    fetchCount = 0

    def gotEntry(msg):
        global fetchCount
        fetchCount += 1
        sys.stdout.write(msg.text.encode("utf8") + "\n")

    page = 1
    while True:
        fetchCount = 0
        sys.stderr.write("Fetching page %d for %s\n" % (page, user))
        d = tw.user_timeline(gotEntry, user, {'count': '200', 'page': str(page)})
        page += 1
        wfd = defer.waitForDeferred(d)
        yield wfd
        wfd.getResult()

        if fetchCount == 0:
            reactor.stop()

user = sys.argv[1]
if len(sys.argv) > 3:
    user = sys.argv[3]

tw = twitter.Twitter(sys.argv[1], sys.argv[2])

defer.maybeDeferred(getSome, tw, user)

reactor.run()
