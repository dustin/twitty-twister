#!/usr/bin/env python
"""

Copyright (c) 2008  Dustin Sallings <dustin@spy.net>
"""

import os
import sys

sys.path.append(os.path.join(sys.path[0], '..', 'twittytwister'))
sys.path.append('twittytwister')

from twisted.internet import reactor, protocol, defer, task

import twitter

def cb(x):
    print "Posted id", x

def eb(e):
    print e

#test this with a small timeout (ie. 0.01) if you want to see a timeout failure
twitter.Twitter(sys.argv[1], sys.argv[2], timeout=float(sys.argv[3])).update(' '.join(sys.argv[4:])
    ).addCallback(cb).addErrback(eb).addBoth(lambda x: reactor.stop())

reactor.run()
