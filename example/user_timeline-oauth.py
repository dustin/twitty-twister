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

def gotEntry(msg):
    print "%s" % (msg.text)

consumer = toauth.OAuthConsumer(sys.argv[1], sys.argv[2])
token = toauth.OAuthToken(sys.argv[3], sys.argv[4])

user = None
if len(sys.argv) > 5:
    user = sys.argv[5]

twitter.Twitter(consumer=consumer, token=token).user_timeline(gotEntry, user).addBoth(
    lambda x: reactor.stop())

reactor.run()
