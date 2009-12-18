#!/usr/bin/env python
"""

Copyright (c) 2008  Dustin Sallings <dustin@spy.net>
Copyright (c) 2009  Eduardo Habkost <ehabkost@raisama.net>

"""

import os
import sys

sys.path.append(os.path.join(sys.path[0], '..', 'twittytwister'))
sys.path.append('twittytwister')

from twisted.internet import reactor, protocol, defer, task

import twitter

def gotId(data):
    print "Friend ID: %s" % (data)

def error(e):
    print "ERROR: ",e

twitter.Twitter(sys.argv[1], sys.argv[2]).friends_ids(gotId, sys.argv[3]).addErrback(error).addBoth(
    lambda x: reactor.stop())

reactor.run()
