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

def cb(x):
    print "Avatar updated"

def eb(e):
    print e

def both(x):
    avatar.close()
    reactor.stop()


consumer = toauth.OAuthConsumer(sys.argv[1], sys.argv[2])
token = toauth.OAuthToken(sys.argv[3], sys.argv[4])
avatar = open(sys.argv[5], 'r')


twitter.Twitter(consumer=consumer, token=token).update_profile_image('avatar.jpg', avatar.read()).addCallback(cb).addErrback(eb).addBoth(both)

reactor.run()
