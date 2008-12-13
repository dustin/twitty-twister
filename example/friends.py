#!/usr/bin/env python
"""

Copyright (c) 2008  Dustin Sallings <dustin@spy.net>
"""

import os
import sys

sys.path.append(os.path.join(sys.path[0], '..', 'lib'))
sys.path.append('lib')

from twisted.internet import reactor, protocol, defer, task

import twitter

def gotEntry(msg):
    print "Got a entry from %s: %s" % (msg.user.screen_name, msg.text)

twitter.Twitter(sys.argv[1], sys.argv[2]).friends(gotEntry).addBoth(
    lambda x: reactor.stop())

reactor.run()
