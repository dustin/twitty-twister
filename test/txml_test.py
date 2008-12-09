#!/usr/bin/env python
"""

Copyright (c) 2008  Dustin Sallings <dustin@spy.net>
"""

from __future__ import with_statement

import sys
sys.path.append("lib")
sys.path.append("../lib")

import unittest

import txml

class XMLParserTest(unittest.TestCase):

    def testParsingEntry(self):
        ts=self
        def gotEntry(e):
            if e.id == 'tag:search.twitter.com,2005:1043835074':
                ts.assertEquals('2008-12-07T19:50:01Z', e.published)
                ts.assertEquals('PlanetAmerica (PlanetAmerica)', e.author.name)
                ts.assertEquals('http://twitter.com/PlanetAmerica',
                    e.author.uri)
                ts.assertEquals(
                    'http://twitter.com/PlanetAmerica/statuses/1043835074',
                    e.alternate)
                ts.assertEquals(
                    'http://s3.amazonaws.com/twitter_production/'
                    'profile_images/66422442/PA_PeaceOnEarth_normal.JPG',
                    e.image)
                ts.assertEquals(
                    '@americac2c getting ready to go out to run errands...'
                    ' If I can just stop tweeting...'
                    ' TWITTER IS LIKE CRACK!', e.title)
                ts.assertEquals(
                    '&lt;a href="http://twitter.com/americac2c"&gt;'
                    '@americac2c&lt;/a&gt; getting ready to go out '
                    'to run errands... If I can just stop tweeting... '
                    '&lt;b&gt;TWITTER&lt;/b&gt; IS LIKE CRACK!',
                     e.content)
        t = txml.Feed(gotEntry)
        f=open("test/search.atom")
        d=f.read()
        f.close()
        t.write(d)
        f.close()

    def testParsingUser(self):
        ts=self
        def gotUser(u):
            if u.id == '16957618':
                ts.assertEquals('16957618', u.id)
                ts.assertEquals('Greg Yaitanes', u.name)
                ts.assertEquals('GregYaitanes', u.screen_name)
                ts.assertEquals('LA or NYC', u.location)
                ts.assertEquals(
                    'twitter investor, advisor and i direct things',
                    u.description)
                ts.assertEquals('http://s3.amazonaws.com/twitter_production/'
                    'profile_images/62795863/gybiopic_normal.jpg',
                    u.profile_image_url)
                ts.assertEquals('http://www.imdb.com/name/nm0944981/', u.url)
                ts.assertEquals('true', u.protected)
                ts.assertEquals('36', u.followers_count)
        f=open("test/friends.xml")
        d=f.read()
        t = txml.Users(gotUser)
        f.close()
        t.write(d)

    def testStatusUpdateParse(self):
        with open("test/update.xml") as f:
            id = txml.parseUpdateResponse(f.read())
            self.assertEquals('1045518625', id)

if __name__ == '__main__':
    unittest.main()
