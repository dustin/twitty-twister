#!/usr/bin/env python
"""

Copyright (c) 2008  Dustin Sallings <dustin@spy.net>
"""

import sys

from twisted.internet import reactor

from twittytwister import twitter

def cb(x):
    print "Posted id", x

def eb(e):
    print e

twitter.Twitter(sys.argv[1], sys.argv[2]).update(' '.join(sys.argv[3:])
    ).addCallback(cb).addErrback(eb).addBoth(lambda x: reactor.stop())

reactor.run()
