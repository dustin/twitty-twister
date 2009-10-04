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

def cb(x):
    print "Posted id", x

def eb(e):
    print e

#set client info
#beware that if you want to use your own client name you should
#talk about it in the twitter development mailing list so they can
#add it, or else it will show up as being 'from web'
info = twitter.TwitterClientInfo('TweetDeck', '1.0', 'http://tweetdeck.com/')
twitter.Twitter(sys.argv[1], sys.argv[2], client_info = info).update(' '.join(sys.argv[3:])
    ).addCallback(cb).addErrback(eb).addBoth(lambda x: reactor.stop())

reactor.run()
