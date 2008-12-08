#!/usr/bin/env python
"""

Copyright (c) 2008  Dustin Sallings <dustin@spy.net>
"""

import sys
sys.path.append("lib")
sys.path.append("../lib")

import unittest

import txml

class XMLParserTest(unittest.TestCase):

    def testParsing(self):
        ts=self
        class D(object):
            def gotEntry(self, e):
                if e.id == 'tag:search.twitter.com,2005:1043835074':
                    ts.assertEquals('2008-12-07T19:50:01Z', e.published)
                    ts.assertEquals('PlanetAmerica (PlanetAmerica)',
                        e.author.name)
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
        t = txml.Feed(D())
        f=open("test/search.atom")
        d=f.read()
        f.close()
        t.write(d)
        f.close()

if __name__ == '__main__':
    unittest.main()
