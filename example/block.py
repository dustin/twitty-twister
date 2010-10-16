#!/usr/bin/env python
"""

Copyright (c) 2008  Dustin Sallings <dustin@spy.net>
"""

import sys

from twisted.internet import reactor

from twittytwister import twitter

def cb(answer):
    def f(x):
        print answer
    return f

twitter.Twitter(sys.argv[1], sys.argv[2]).block(sys.argv[3]).addCallback(
    cb("worked")).addErrback(cb("didn't work")).addBoth(
    lambda x: reactor.stop())

reactor.run()
