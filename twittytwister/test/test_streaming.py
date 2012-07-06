# Copyright (c) 2010-2012 Ralph Meijer <ralphm@ik.nu>
# See LICENSE.txt for details

"""
Tests for L{twittytwister.streaming}.
"""

from twisted.internet import task
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
        self.keepAlives = 0


    def datagramReceived(self, data):
        self.datagrams.append(data)


    def keepAliveReceived(self):
        self.keepAlives += 1



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
        self.assertEquals(0, self.protocol.keepAlives)


    def test_receiveTwoDatagrams(self):
        """
        Two encoded datagrams should result in two calls to datagramReceived.
        """
        self.protocol.dataReceived("""4\r\ntest5\r\ntest2""")
        self.assertEquals(['test', 'test2'], self.protocol.datagrams)
        self.assertEquals(0, self.protocol.keepAlives)


    def test_receiveKeepAlive(self):
        """
        Datagrams may have empty keep-alive lines in between.
        """
        self.protocol.dataReceived("""4\r\ntest\r\n5\r\ntest2""")
        self.assertEquals(['test', 'test2'], self.protocol.datagrams)
        self.assertEquals(1, self.protocol.keepAlives)


    def test_notImplemented(self):
        self.protocol = streaming.LengthDelimitedStream()
        self.assertRaises(NotImplementedError, self.protocol.dataReceived,
                                               """4\r\ntest""")



class TwitterObjectTest(unittest.TestCase):
    """
    Tests for L{streaming.TwitterObject} and subclasses.
    """

    def setUp(self):
        self.data = [
            {
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
                    'verified': False}},
            {
                "text": "#Photos on Twitter: taking flight http://t.co/qbJx26r",
                "entities": {
                    "media": [
                        {
                            "id": 76360760611180544,
                            "id_str": "76360760611180544",
                            "media_url": "http://p.twimg.com/AQ9JtQsCEAA7dEN.jpg",
                            "media_url_https": "https://p.twimg.com/AQ9JtQsCEAA7dEN.jpg",
                            "url": "http://t.co/qbJx26r",
                            "display_url": "pic.twitter.com/qbJx26r",
                            "expanded_url": "http://twitter.com/twitter/status/76360760606986241/photo/1",
                            "sizes": {
                                "large": {
                                    "w": 700,
                                    "resize": "fit",
                                    "h": 466
                                },
                                "medium": {
                                    "w": 600,
                                    "resize": "fit",
                                    "h": 399
                                },
                                "small": {
                                    "w": 340,
                                    "resize": "fit",
                                    "h": 226
                                },
                                "thumb": {
                                    "w": 150,
                                    "resize": "crop",
                                    "h": 150
                                }
                            },
                            "type": "photo",
                            "indices": [
                                34,
                                53
                            ]
                        }
                    ],
                    "urls": [],
                    "user_mentions": [],
                    "hashtags": []
                }
            }
        ]


    def test_fromDictBasic(self):
        """
        A tweet is a Status with a user attribute holding a User.
        """

        status = streaming.Status.fromDict(self.data[0])
        self.assertEquals(u'Test #1', status.text)
        self.assertEquals(70393696, status.user.id)
        self.assertEquals(u'ikdisplay', status.user.screen_name)


    def test_fromDictEntitiesMediaBasic(self):
        """
        Media entities are parsed, simple properties are available.
        """

        status = streaming.Status.fromDict(self.data[1])
        self.assertTrue(hasattr(status.entities, 'media'))
        self.assertTrue(hasattr(status.entities, 'urls'))
        self.assertTrue(hasattr(status.entities, 'user_mentions'))
        self.assertTrue(hasattr(status.entities, 'hashtags'))
        self.assertEqual(1, len(status.entities.media))
        mediaItem = status.entities.media[0]
        self.assertEqual(76360760611180544, mediaItem.id)
        self.assertEqual('http://p.twimg.com/AQ9JtQsCEAA7dEN.jpg',
                         mediaItem.media_url)


    def test_fromDictEntitiesMediaIndices(self):
        """
        Media entities are parsed, simple properties are available.
        """

        status = streaming.Status.fromDict(self.data[1])
        mediaItem = status.entities.media[0]
        self.assertEquals(34, mediaItem.indices.start)
        self.assertEquals(53, mediaItem.indices.end)


    def test_fromDictEntitiesMediaSizes(self):
        """
        Media sizes are extracted.
        """

        status = streaming.Status.fromDict(self.data[1])
        mediaItem = status.entities.media[0]
        self.assertEquals(700, mediaItem.sizes.large.w)
        self.assertEquals(466, mediaItem.sizes.large.h)
        self.assertEquals('fit', mediaItem.sizes.large.resize)


    def test_fromDictEntitiesURL(self):
        """
        URL entities are extracted.
        """
        data = {
            "urls": [
                {
                    "url": "http://t.co/0JG5Mcq",
                    "display_url": u"blog.twitter.com/2011/05/twitte\xe2",
                    "expanded_url": "http://blog.twitter.com/2011/05/twitter-for-mac-update.html",
                    "indices": [
                        84,
                        103
                    ]
                }
            ],
        }
        entities = streaming.Entities.fromDict(data)
        self.assertEquals('http://t.co/0JG5Mcq', entities.urls[0].url)


    def test_fromDictEntitiesUserMention(self):
        """
        User mention entities are extracted.
        """
        data = {
            "user_mentions": [
                {
                    "id": 22548447,
                    "id_str": "22548447",
                    "screen_name": "rno",
                    "name": "Arnaud Meunier",
                    "indices": [
                        0,
                        4
                    ]
                }
            ],
        }
        entities = streaming.Entities.fromDict(data)
        user_mention = entities.user_mentions[0]
        self.assertEquals(22548447, user_mention.id)
        self.assertEquals('rno', user_mention.screen_name)
        self.assertEquals('Arnaud Meunier', user_mention.name)
        self.assertEquals(0, user_mention.indices.start)
        self.assertEquals(4, user_mention.indices.end)


    def test_fromDictEntitiesHashTag(self):
        """
        Hash tag entities are extracted.
        """
        data = {
            "hashtags": [
                {
                    "text": "devnestSF",
                    "indices": [
                        6,
                        16
                    ]
                }
            ]
        }
        entities = streaming.Entities.fromDict(data)
        hashTag = entities.hashtags[0]
        self.assertEquals('devnestSF', hashTag.text)
        self.assertEquals(6, hashTag.indices.start)
        self.assertEquals(16, hashTag.indices.end)


    def test_repr(self):
        data = {
                'created_at': 'Mon Dec 06 11:46:33 +0000 2010',
                'entities': {'hashtags': [], 'urls': [], 'user_mentions': []},
                'id': 11748322888908800,
                'text': 'Test #1',
                'user': {
                    'id': 70393696,
                    'screen_name': 'ikdisplay',
                    }
                }
        status = streaming.Status.fromDict(data)
        result = repr(status)
        expected = """Status(
    created_at='Mon Dec 06 11:46:33 +0000 2010',
    entities=Entities(
        hashtags=[],
        urls=[],
        user_mentions=[]
    ),
    id=11748322888908800,
    text='Test #1',
    user=User(
        id=70393696,
        screen_name='ikdisplay'
    )
)"""
        self.assertEqual(expected, result)


    def test_reprIndices(self):
        data = [6, 16]
        indices = streaming.Indices.fromDict(data)
        result = repr(indices)
        expected = """Indices(start=6, end=16)"""
        self.assertEqual(expected, result)


    def test_reprEntities(self):
        data = {
            "urls": [
                {
                    "url": "http://t.co/0JG5Mcq",
                    "display_url": u"blog.twitter.com/2011/05/twitte\xe2",
                    "expanded_url": "http://blog.twitter.com/2011/05/twitter-for-mac-update.html",
                    "indices": [
                        84,
                        103
                    ]
                }
            ],
        }
        entities = streaming.Entities.fromDict(data)
        result = repr(entities)
        expected = """Entities(
    urls=[
        URL(
            display_url=u'blog.twitter.com/2011/05/twitte\\xe2',
            expanded_url='http://blog.twitter.com/2011/05/twitter-for-mac-update.html',
            indices=Indices(start=84, end=103),
            url='http://t.co/0JG5Mcq'
        )
    ]
)"""
        self.assertEqual(expected, result)


class TestableTwitterStream(streaming.TwitterStream):

    def __init__(self, _clock, *args, **kwargs):
        self._clock = _clock
        streaming.TwitterStream.__init__(self, *args, **kwargs)


    def callLater(self, *args, **kwargs):
        return self._clock.callLater(*args, **kwargs)



class TwitterStreamTest(unittest.TestCase):
    """
    Tests for L{streaming.TwitterStream}.
    """

    def setUp(self):
        self.objects = []
        self.transport = proto_helpers.StringTransport()
        self.clock = task.Clock()
        self.protocol = TestableTwitterStream(self.clock, self.objects.append)
        self.protocol.makeConnection(self.transport)


    def tearDown(self):
        self.protocol.setTimeout(None)


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


    def test_closedNoTimeout(self):
        """
        When the connection is done, there is no timeout.
        """
        self.protocol.connectionLost(failure.Failure(ResponseDone()))
        self.assertEquals(None, self.protocol.timeOut)
        return self.protocol.deferred


    def test_timeout(self):
        """
        When the timeout is reached, the transport should stop producing.

        A real transport would call connectionLost, but we don't need to test
        that here.
        """
        self.clock.advance(59)
        self.assertEquals('producing', self.transport.producerState)
        self.clock.advance(1)
        self.assertEquals('stopped', self.transport.producerState)


    def test_timeoutPostponedOnData(self):
        """
        When the timeout is reached, the transport stops producing.

        A real transport would call connectionLost, but we don't need to test
        that here.
        """
        self.clock.advance(20)
        data = """{"text": "Test status"}\n\r"""
        self.protocol.dataReceived(data)
        self.clock.advance(40)
        self.assertEquals('producing', self.transport.producerState,
                          "Unexpected timeout")
        self.clock.advance(20)
        self.assertEquals('stopped', self.transport.producerState)
