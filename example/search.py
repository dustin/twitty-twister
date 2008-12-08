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

class CB(object):
    def gotEntry(self, msg):
        print "Got a entry: ", msg.title

twitter.search(sys.argv[1], CB()).addBoth(lambda x: reactor.stop())

reactor.run()
