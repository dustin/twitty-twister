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

proxy_host = "my_proxy_host"
proxy_port = 80  # 80 is the default
proxy_username = "username"
proxy_password = "secret"

twitter.TwitterFeed(u, p, proxy_host=proxy_host, proxy_port=proxy_port,
        proxy_username=proxy_username, proxy_password=proxy_password
        ).track(cb, set(terms)).addErrback(log.err)

reactor.run()
