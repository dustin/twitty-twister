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

twitter.TwitterFeed(sys.argv[1], sys.argv[2]).spritzer(cb).addErrback(log.err)

reactor.run()
