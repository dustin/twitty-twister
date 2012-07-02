#!/usr/bin/env python
#
# Copyright (c) 2012  Ralph Meijer <ralphm@ik.nu>
# See LICENSE.txt for details

"""
Print Tweets on a user's timeline in real time.

This connects to the Twitter User Stream API endpoint with the given OAuth
credentials and prints out all Tweets of the associated user and of the
accounts the user follows. This is equivalent to the user's time line.

The arguments, in order, are: consumer key, consumer secret, access token key,
access token secret.
"""

import sys

from twisted.internet import reactor
from twisted.python import log

from oauth import oauth

from twittytwister import twitter

def cb(entry):
    print '%s: %s' % (entry.user.screen_name.encode('utf-8'),
                      entry.text.encode('utf-8'))

consumer = oauth.OAuthConsumer(sys.argv[1], sys.argv[2])
token = oauth.OAuthToken(sys.argv[3], sys.argv[4])

feed = twitter.TwitterFeed(consumer=consumer, token=token)
d = feed.user(cb, {'with': 'followings'})

# Exit when the connection was closed or an exception was raised.
d.addCallback(lambda protocol: protocol.deferred)
d.addErrback(log.err)
d.addBoth(lambda _: reactor.stop())

reactor.run()
