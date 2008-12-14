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

    def parse_test(self, filename, parser):
        with open(filename) as f:
            parser.write(f.read())

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
        self.parse_test('test/search.atom', txml.Feed(gotEntry))

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
        self.parse_test('test/friends.xml', txml.Users(gotUser))

    def testParsingDirectMessages(self):
        ts=self
        def gotDirectMessage(dm):
            ts.assertEquals('45010464', dm.id)
            ts.assertEquals('24113688', dm.sender_id)
            ts.assertEquals('some stuff', dm.text)
            ts.assertEquals('14117412', dm.recipient_id)
            ts.assertEquals('Fri Dec 12 17:50:50 +0000 2008', dm.created_at)
            ts.assertEquals('somesender', dm.sender_screen_name)
            ts.assertEquals('dlsspy', dm.recipient_screen_name)

            ts.assertEquals('24113688', dm.sender.id)
            ts.assertEquals('Some Sender', dm.sender.name)
            ts.assertEquals('somesender', dm.sender.screen_name)
            ts.assertEquals('Some Place', dm.sender.location)
            ts.assertEquals('I do stuff.', dm.sender.description)
            ts.assertEquals('http://www.spy.net/obama-hornz.jpg',
                dm.sender.profile_image_url)
            ts.assertEquals('http://www.spy.net/', dm.sender.url)
            ts.assertEquals('false', dm.sender.protected)
            ts.assertEquals('76', dm.sender.followers_count)

            ts.assertEquals('14117412', dm.recipient.id)
            ts.assertEquals('Dustin Sallings', dm.recipient.name)
            ts.assertEquals('dlsspy', dm.recipient.screen_name)
            ts.assertEquals('Santa Clara, CA', dm.recipient.location)
            ts.assertEquals('Probably writing code.', dm.recipient.description)
            ts.assertEquals('http://s3.amazonaws.com/twitter_production/'
                'profile_images/57455325/IMG_0596_2_normal.JPG',
                dm.recipient.profile_image_url)
            ts.assertEquals('http://bleu.west.spy.net/~dustin/',
                dm.recipient.url)
            ts.assertEquals('false', dm.recipient.protected)
            ts.assertEquals('198', dm.recipient.followers_count)
        self.parse_test('test/dm.xml', txml.Direct(gotDirectMessage))

    def testParsingStatusList(self):
        ts=self
        def gotStatusItem(s):
            if s.id == '1054780802':
                ts.assertEquals('1054780802', s.id)
                ts.assertEquals('Sat Dec 13 04:10:57 +0000 2008', s.created_at)
                ts.assertEquals('Getting Jekyll ready for something '
                    'special next week.', s.text)
                ts.assertEquals('false', s.truncated)
                ts.assertEquals('', s.in_reply_to_status_id)
                ts.assertEquals('', s.in_reply_to_user_id)
                ts.assertEquals('false', s.favorited)
                ts.assertEquals('', s.in_reply_to_screen_name)
                ts.assertEquals('5502392', s.user.id)
                ts.assertEquals('Tom Preston-Werner', s.user.name)
                ts.assertEquals('mojombo', s.user.screen_name)
                ts.assertEquals('iPhone: 37.813461,-122.416519',
                    s.user.location)
                ts.assertEquals('powerset ftw!', s.user.description)
                ts.assertEquals('http://s3.amazonaws.com/twitter_production/'
                    'profile_images/21599172/tom_prestonwerner_normal.jpg',
                    s.user.profile_image_url)
                ts.assertEquals('http://rubyisawesome.com', s.user.url)
                ts.assertEquals('false', s.user.protected)
                ts.assertEquals('516', s.user.followers_count)

        self.parse_test('test/status_list.xml', txml.StatusList(gotStatusItem))

    def testParsingUser(self):
        ts = self
        def gotUser(u):
            ts.assertEquals('14117412', u.id)
            ts.assertEquals('Dustin Sallings', u.name)
            ts.assertEquals('dlsspy', u.screen_name)
            ts.assertEquals('Santa Clara, CA', u.location)
            ts.assertEquals('Probably writing code.', u.description)
            ts.assertEquals('http://s3.amazonaws.com/twitter_production/'
                'profile_images/57455325/IMG_0596_2_normal.JPG',
                u.profile_image_url)
            ts.assertEquals('http://bleu.west.spy.net/~dustin/', u.url)
            ts.assertEquals('false', u.protected)
            ts.assertEquals('201', u.followers_count)
            ts.assertEquals('9ae4e8', u.profile_background_color)
            ts.assertEquals('000000', u.profile_text_color)
            ts.assertEquals('0000ff', u.profile_link_color)
            ts.assertEquals('e0ff92', u.profile_sidebar_fill_color)
            ts.assertEquals('87bc44', u.profile_sidebar_border_color)
            ts.assertEquals('54', u.friends_count)
            ts.assertEquals('Mon Mar 10 20:57:07 +0000 2008', u.created_at)
            ts.assertEquals('37', u.favourites_count)
            ts.assertEquals('-28800', u.utc_offset)
            # ts.assertEquals('Pacific Time (US & Canada)', u.time_zone)
            ts.assertEquals('false', u.following)
            ts.assertEquals('false', u.notifications)
            ts.assertEquals('1583', u.statuses_count)
            ts.assertEquals('Sun Dec 14 07:24:26 +0000 2008',
                u.status.created_at)
            ts.assertEquals('1056508954', u.status.id)
            ts.assertEquals('Never before have so many people with so '
                'little to say said so much to so few. '
                'http://despair.com/blogging.html', u.status.text)
            # ts.assertEquals(
            #     '<a href="http://github.com/dustin/twitterspy">TwitterSpy< a>',
            #     u.status.source)
            ts.assertEquals('false', u.status.truncated)
            ts.assertEquals('', u.status.in_reply_to_status_id)
            ts.assertEquals('', u.status.in_reply_to_user_id)
            ts.assertEquals('false', u.status.favorited)
            ts.assertEquals('', u.status.in_reply_to_screen_name)

        self.parse_test('test/user.xml', txml.Users(gotUser))

    def testStatusUpdateParse(self):
        with open("test/update.xml") as f:
            id = txml.parseUpdateResponse(f.read())
            self.assertEquals('1045518625', id)

if __name__ == '__main__':
    unittest.main()
