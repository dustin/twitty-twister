#!/usr/bin/env python
"""

Copyright (c) 2008  Dustin Sallings <dustin@spy.net>
"""

import sys

from twisted.internet import reactor
from twisted.python import log

from twittytwister import twitter

def cb(entry):
    print entry.text

u, p, terms = sys.argv[1], sys.argv[2], sys.argv[3:]

twitter.TwitterFeed(u, p).track(cb, set(terms)).addErrback(log.err)

reactor.run()
