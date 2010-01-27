#!/usr/bin/env python
"""

Copyright (c) 2008  Dustin Sallings <dustin@spy.net>
"""

import os
import sys

from twisted.internet import reactor, protocol, defer, task

from twittytwister import twitter

def gotEntry(msg):
    print "Got a entry: ", msg.title

twitter.Twitter().search(sys.argv[1], gotEntry).addBoth(
    lambda x: reactor.stop())

reactor.run()
