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

This is mostly the same as the C{user_stream.py} example, except that this
uses L{twittytwisted.streaming.TwitterMonitor}. It will reconnect in the
face of disconnections or explicit reconnects to change the API request
parameters (e.g. changing the track keywords).
"""

import sys

from twisted.internet import reactor

from oauth import oauth

from twittytwister import twitter

def cb(entry):
    print '%s: %s' % (entry.user.screen_name.encode('utf-8'),
                      entry.text.encode('utf-8'))

def change(monitor):
    monitor.args = {}
    monitor.connect(forceReconnect=True)

consumer = oauth.OAuthConsumer(sys.argv[1], sys.argv[2])
token = oauth.OAuthToken(sys.argv[3], sys.argv[4])

feed = twitter.TwitterFeed(consumer=consumer, token=token)
monitor = twitter.TwitterMonitor(feed.user, cb, {'with': 'followings'})

monitor.startService()
reactor.callLater(30, change, monitor)

reactor.run()
