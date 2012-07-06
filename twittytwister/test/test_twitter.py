# Copyright (c) 2010-2012  Ralph Meijer <ralphm@ik.nu>
# See LICENSE.txt for details

"""
Tests for L{twittytwister.twitter}.
"""

from twisted.trial import unittest
from twittytwister import twitter

class TwitterFeedTest(unittest.TestCase):
    """
    Tests for L{twitter.TwitterFeed):
    """

    def setUp(self):
        self.feed = twitter.TwitterFeed()
        self.calls = []


    def _rtfeed(self, url, delegate, args):
        self.calls.append((url, delegate, args))


    def test_user(self):
        """
        C{user} opens a Twitter User Stream.
        """
        self.patch(self.feed, '_rtfeed', self._rtfeed)
        self.feed.user(None)
        self.assertEqual(1, len(self.calls))
        url, delegate, args = self.calls[-1]
        self.assertEqual('https://userstream.twitter.com/2/user.json', url)
        self.assertIdentical(None, delegate)
        self.assertIdentical(None, args)


    def test_userArgs(self):
        """
        The second argument to C{user} is a dict passed on as arguments.
        """
        self.patch(self.feed, '_rtfeed', self._rtfeed)
        self.feed.user(None, {'replies': 'all'})
        url, delegate, args = self.calls[-1]
        self.assertEqual({'replies': 'all'}, args)


    def test_site(self):
        """
        C{site} opens a Twitter Site Stream.
        """
        self.patch(self.feed, '_rtfeed', self._rtfeed)
        self.feed.site(None, {'follow': '6253282'})
        self.assertEqual(1, len(self.calls))
        url, delegate, args = self.calls[-1]
        self.assertEqual('https://sitestream.twitter.com/2b/site.json', url)
        self.assertIdentical(None, delegate)
        self.assertEqual({'follow': '6253282'}, args)
