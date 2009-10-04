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

def gotUser(u):
    print "Got a user: %s" % u

consumer = toauth.OAuthConsumer(sys.argv[1], sys.argv[2])
token = toauth.OAuthToken(sys.argv[3], sys.argv[4])

twitter.Twitter(consumer=consumer, token=token).show_user(sys.argv[5]).addCallback(
    gotUser).addBoth(lambda x: reactor.stop())

reactor.run()
