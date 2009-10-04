#!/usr/bin/env python
"""

Copyright (c) 2009  Kevin Dunglas <dunglas@gmail.com>
"""

import os
import sys

sys.path.append(os.path.join(sys.path[0], '..', 'lib'))
sys.path.append('lib')

from twisted.internet import reactor

import twitter
import toauth

def gotUser(user):
    print "User:  %s (%s)" % (user.name, user.screen_name)

un=None
if len(sys.argv) > 5:
    un=sys.argv[5]

consumer = toauth.OAuthConsumer(sys.argv[1], sys.argv[2])
token = toauth.OAuthToken(sys.argv[3], sys.argv[4])

twitter.Twitter(consumer=consumer, token=token).list_friends(gotUser, un).addBoth(
    lambda x: reactor.stop())

reactor.run()
