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
import oauth

def cb(x):
    print "Posted id", x

def eb(e):
    print e

consumer = oauth.OAuthConsumer(sys.argv[1], sys.argv[2])
token = oauth.OAuthToken(sys.argv[3], sys.argv[4])

twitter.Twitter(consumer=consumer, token=token).update(' '.join(sys.argv[5:])
    ).addCallback(cb).addErrback(eb).addBoth(lambda x: reactor.stop())

reactor.run()