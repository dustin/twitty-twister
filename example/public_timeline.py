#!/usr/bin/env python
"""

Copyright (c) 2009  tsing <tsing@jianqing.org>
"""

import os
import sys

sys.path.append(os.path.join(sys.path[0], '..', 'twittytwister'))
sys.path.append('twittytwister')

from twisted.internet import reactor, protocol, defer, task

import twitter

def gotEntry(msg):
    print "Got a entry from %s: %s" % (msg.author.name, msg.title)

twitter.Twitter(sys.argv[1], sys.argv[2]).public_timeline(gotEntry).addBoth(
    lambda x: reactor.stop())

reactor.run()
