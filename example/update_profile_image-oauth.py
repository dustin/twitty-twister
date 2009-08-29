#!/usr/bin/env python
"""
Copyright (c) 2009  Kevin Dunglas <dunglas@gmail.com>
"""

import os
import sys

from twisted.internet import reactor

from twittytwister import twitter
import oauth

def cb(x):
    print "Avatar updated"

def eb(e):
    print e

def both(x):
    avatar.close()
    reactor.stop()


consumer = oauth.OAuthConsumer(sys.argv[1], sys.argv[2])
token = oauth.OAuthToken(sys.argv[3], sys.argv[4])
avatar = open(sys.argv[5], 'r')


twitter.Twitter(consumer=consumer, token=token).update_profile_image('avatar.jpg', avatar.read()).addCallback(cb).addErrback(eb).addBoth(both)

reactor.run()