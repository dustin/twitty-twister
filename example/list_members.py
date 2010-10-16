#!/usr/bin/env python
"""

Copyright (c) 2008  Dustin Sallings <dustin@spy.net>
Copyright (c) 2009  Bogdano Arendartchuk <debogdano@gmail.com>
"""

import os
import sys

from twisted.internet import reactor, protocol, defer, task

from twittytwister import twitter

def gotEntry(msg):
    print "Got a entry from %s" % repr(msg.screen_name)

twitter.Twitter(sys.argv[1], sys.argv[2]).list_members(gotEntry, sys.argv[3],
        sys.argv[4]).addBoth(lambda x: reactor.stop())

reactor.run()
