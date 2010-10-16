#!/usr/bin/env python
"""

Copyright (c) 2008  Dustin Sallings <dustin@spy.net>
"""

import sys

from twisted.internet import reactor

from twittytwister import twitter

def gotEntry(msg):
    print "Got a entry from %s: %s" % (msg.user.screen_name, msg.text)

twitter.Twitter(sys.argv[1], sys.argv[2]).friends(gotEntry).addBoth(
    lambda x: reactor.stop())

reactor.run()
