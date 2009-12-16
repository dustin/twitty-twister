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

def gotUser(user):
    print "User:  %s (%s)" % (user.name, user.screen_name)

def error(e):
    print "ERROR: %s" % (e)
    reactor.stop()

un=None
if len(sys.argv) > 3:
    un=sys.argv[3]

twitter.Twitter(sys.argv[1], sys.argv[2]).list_friends(gotUser, un).addCallbacks(
    lambda x: reactor.stop(), error)

reactor.run()
