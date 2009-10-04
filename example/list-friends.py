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

un=None
if len(sys.argv) > 3:
    un=sys.argv[3]

twitter.Twitter(sys.argv[1], sys.argv[2]).list_friends(gotUser, un).addBoth(
    lambda x: reactor.stop())

reactor.run()
