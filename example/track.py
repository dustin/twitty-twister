#!/usr/bin/env python
"""

Copyright (c) 2008  Dustin Sallings <dustin@spy.net>
"""

import os
import sys

sys.path.append(os.path.join(sys.path[0], '..', 'lib'))
sys.path.append('lib')

from twisted.internet import reactor, protocol, defer, task
from twisted.python import log

import twitter

def cb(entry):
    print entry.text

u, p, terms = sys.argv[1], sys.argv[2], sys.argv[3:]

twitter.TwitterFeed(u, p).track(cb, set(terms)).addErrback(log.err)

reactor.run()
