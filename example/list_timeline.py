#!/usr/bin/env python
"""

Copyright (c) 2008  Dustin Sallings <dustin@spy.net>
Copyright (c) 2009  Bogdano Arendartchuk <debogdano@gmail.com>
"""

import sys

from twisted.internet import reactor, defer

from twittytwister import twitter

fetchCount = 0

@defer.deferredGenerator
def getSome(tw, list_user, list_name):
    global fetchCount
    fetchCount = 0

    def gotEntry(msg):
        global fetchCount
        fetchCount += 1
        sys.stdout.write(msg.text.encode("utf8") + "\n")

    page = 1
    while True:
        fetchCount = 0
        sys.stderr.write("Fetching page %d for %s/%s\n" % (page, list_user,
            list_name))
        d = tw.list_timeline(gotEntry, list_user, list_name,
                {'count': '200', 'page': str(page)})
        page += 1
        wfd = defer.waitForDeferred(d)
        yield wfd
        wfd.getResult()

        if fetchCount == 0:
            reactor.stop()

user = sys.argv[1]
list_user = sys.argv[3]
list_name = sys.argv[4]

tw = twitter.Twitter(sys.argv[1], sys.argv[2])

defer.maybeDeferred(getSome, tw, list_user, list_name)

reactor.run()
