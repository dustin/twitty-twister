#!/usr/bin/env python
"""

Copyright (c) 2008  Dustin Sallings <dustin@spy.net>
"""

import sys

from twisted.internet import reactor

from twittytwister import twitter

def gotUser(user):
    print "User:  %s (%s)" % (user.name, user.screen_name)

un=None
if len(sys.argv) > 3:
    un=sys.argv[3]

twitter.Twitter(sys.argv[1], sys.argv[2]).list_followers(gotUser, un).addBoth(
    lambda x: reactor.stop())

reactor.run()
