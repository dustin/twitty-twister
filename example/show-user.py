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

def gotUser(u):
    print "Got a user: %s" % u

twitter.Twitter(sys.argv[1], sys.argv[2]).show_user(sys.argv[3]).addCallback(
    gotUser).addBoth(lambda x: reactor.stop())

reactor.run()
