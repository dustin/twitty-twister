# Copyright (c) 2010 Ralph Meijer <ralphm@ik.nu>
# See LICENSE.txt for details

"""
Tests for L{twittytwister.streaming}.
"""

from twisted.python import failure
from twisted.test import proto_helpers
from twisted.trial import unittest
from twisted.web.client import ResponseDone
from twisted.web.http import PotentialDataLoss

from twittytwister import streaming

class StreamTester(streaming.LengthDelimitedStream):
    """
    Test helper that stores all received datagrams in sequence.
    """
    def __init__(self):
        streaming.LengthDelimitedStream.__init__(self)
        self.datagrams = []


    def datagramReceived(self, data):
        self.datagrams.append(data)



class LengthDelimitedStreamTest(unittest.TestCase):
    """
    Tests for L{LengthDelimitedStream}.
    """

    def setUp(self):
        transport = proto_helpers.StringTransport()
        self.protocol = StreamTester()
        self.protocol.makeConnection(transport)


    def test_receiveDatagram(self):
        """
        A datagram is a length, CRLF and a sequence of bytes of given length.
        """
        self.protocol.dataReceived("""4\r\ntest""")
        self.assertEquals(['test'], self.protocol.datagrams)


    def test_receiveTwoDatagrams(self):
        """
        Two encoded datagrams should result in two calls to datagramReceived.
        """
        self.protocol.dataReceived("""4\r\ntest5\r\ntest2""")
        self.assertEquals(['test', 'test2'], self.protocol.datagrams)


    def test_receiveKeepAlive(self):
        """
        Datagrams may have empty keep-alive lines in between.
        """
        self.protocol.dataReceived("""4\r\ntest\r\n5\r\ntest2""")
        self.assertEquals(['test', 'test2'], self.protocol.datagrams)


    def test_notImplemented(self):
        self.protocol = streaming.LengthDelimitedStream()
        self.assertRaises(NotImplementedError, self.protocol.dataReceived,
                                               """4\r\ntest""")

class TwitterObjectTest(unittest.TestCase):
    """
    Tests for L{streaming.TwitterObject} and subclasses.
    """

    def setUp(self):
        self.data = {
                'contributors': None,
                'coordinates': None,
                'created_at': 'Mon Dec 06 11:46:33 +0000 2010',
                'entities': {'hashtags': [], 'urls': [], 'user_mentions': []},
                'favorited': False,
                'geo': None,
                'id': 11748322888908800,
                'id_str': '11748322888908800',
                'in_reply_to_screen_name': None,
                'in_reply_to_status_id': None,
                'in_reply_to_status_id_str': None,
                'in_reply_to_user_id': None,
                'in_reply_to_user_id_str': None,
                'place': None,
                'retweet_count': None,
                'retweeted': False,
                'source': 'web',
                'text': 'Test #1',
                'truncated': False,
                'user': {
                    'contributors_enabled': False,
                    'created_at': 'Mon Aug 31 13:36:20 +0000 2009',
                    'description': None,
                    'favourites_count': 0,
                    'follow_request_sent': None,
                    'followers_count': 1,
                    'following': None,
                    'friends_count': 0,
                    'geo_enabled': False,
                    'id': 70393696,
                    'id_str': '70393696',
                    'lang': 'en',
                    'listed_count': 0,
                    'location': None,
                    'name': 'ikDisplay',
                    'notifications': None,
                    'profile_background_color': 'C0DEED',
                    'profile_background_image_url': 'http://s.twimg.com/a/1290538325/images/themes/theme1/bg.png',
                    'profile_background_tile': False,
                    'profile_image_url': 'http://a2.twimg.com/profile_images/494331594/ikTag_normal.png',
                    'profile_link_color': '0084B4',
                    'profile_sidebar_border_color': 'C0DEED',
                    'profile_sidebar_fill_color': 'DDEEF6',
                    'profile_text_color': '333333',
                    'profile_use_background_image': True,
                    'protected': False,
                    'screen_name': 'ikdisplay',
                    'show_all_inline_media': False,
                    'statuses_count': 23,
                    'time_zone': None,
                    'url': None,
                    'utc_offset': None,
                    'verified': False}}


    def test_fromDictBasic(self):
        """
        A tweet is a Status with a user attribute holding a User.
        """
        status = streaming.Status.fromDict(self.data)
        self.assertEquals(u'Test #1', status.text)
        self.assertEquals(70393696, status.user.id)
        self.assertEquals(u'ikdisplay', status.user.screen_name)



class TwitterStreamTest(unittest.TestCase):
    """
    Tests for L{streaming.TwitterStream}.
    """

    def setUp(self):
        self.objects = []
        transport = proto_helpers.StringTransport()
        self.protocol = streaming.TwitterStream(self.objects.append)
        self.protocol.makeConnection(transport)


    def test_status(self):
        """
        Status objects become L{streaming.Status} objects passed to callback.
        """
        data = """{"text": "Test status"}\n\r"""
        self.protocol.datagramReceived(data)
        self.assertEquals(1, len(self.objects))
        self.assertIsInstance(self.objects[-1], streaming.Status)


    def test_unknownObject(self):
        """
        Unknown objects are ignored.
        """
        data = """{"something": "Some Value"}\n\r"""
        self.protocol.datagramReceived(data)
        self.assertEquals(0, len(self.objects))


    def test_badJSON(self):
        """
        Datagrams with invalid JSON are logged and ignored.
        """
        data = """blah\n\r"""
        self.protocol.datagramReceived(data)
        self.assertEquals(0, len(self.objects))
        loggedErrors = self.flushLoggedErrors(ValueError)
        self.assertEquals(1, len(loggedErrors))


    def test_closedResponseDone(self):
        """
        When the connection is done, the deferred is fired.
        """
        self.protocol.connectionLost(failure.Failure(ResponseDone()))
        return self.protocol.deferred


    def test_closedPotentialDataLoss(self):
        """
        When the connection is done, the deferred is fired.
        """
        self.protocol.connectionLost(failure.Failure(PotentialDataLoss()))
        return self.protocol.deferred


    def test_closedOther(self):
        """
        When the connection is done, the deferred is fired.
        """
        self.protocol.connectionLost(failure.Failure(Exception()))
        self.assertFailure(self.protocol.deferred, Exception)
