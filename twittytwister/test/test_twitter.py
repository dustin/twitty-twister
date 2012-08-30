# Copyright (c) 2010-2012  Ralph Meijer <ralphm@ik.nu>
# See LICENSE.txt for details

"""
Tests for L{twittytwister.twitter}.
"""

from twisted.internet import defer, task
from twisted.internet.error import ConnectError
from twisted.python import failure
from twisted.trial import unittest
from twisted.web import error as http_error
from twisted.web.client import ResponseDone
from twisted.web.http import PotentialDataLoss

from twittytwister import twitter

DELAY_INITIAL = twitter.TwitterMonitor.backOffs[None]['initial']

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



class FakeTwitterProtocol(object):
    def __init__(self):
        self.deferred = defer.Deferred()
        self.transport = self
        self.stopCalled = False


    def stopProducing(self):
        self.stopCalled = True


    def connectionLost(self, reason):
        if reason.check(ResponseDone, PotentialDataLoss):
            self.deferred.callback(None)
        else:
            self.deferred.errback(reason)



class FakeTwitterAPI(object):
    """
    Fake TwitterAPI that provides a filter method for testing.
    """

    protocol = None
    deferred = None

    def __init__(self):
        self.filterCalls = []

    def filter(self, *args):
        """
        Returns the deferred, which can be fired in tests at will.
        """
        self.filterCalls.append(args)
        self.deferred = defer.Deferred()
        return self.deferred


    def connected(self):
        self.protocol = FakeTwitterProtocol()
        self.deferred.callback(self.protocol)


    def connectFail(self, reason):
        """
        Fail the connection attempt.
        """
        self.deferred.errback(reason)



class TwitterMonitorTest(unittest.TestCase):
    def setUp(self):
        self.entries = []
        self.clock = task.Clock()
        self.api = FakeTwitterAPI()
        self.monitor = twitter.TwitterMonitor(self.api,
                                              consumer=self,
                                              reactor=self.clock)
        self.connects = None


    def tearDown(self):
        self.assertEquals(0, len(self.clock.calls))


    def onEntry(self, entry):
        self.entries.append(entry)


    def setUpState(self, state):
        """
        Set up the monitor to a given state, to simplify tests.
        """
        # Initial state is 'stopped'.
        if state == 'stopped':
            return

        # Starting the service with no terms or userIDs results in state 'idle'.
        self.monitor.startService()
        if state == 'idle':
            return

        # Setting up filters causes transition to state 'connecting'.
        self.monitor.setFilters(set(['foo', 'bar']), set(['42']))
        self.clock.advance(0)
        if state == 'connecting':
            return

        # If we want to reach aborting, don't connect but set filters again.
        if state == 'aborting':
            self.monitor.setFilters(set(['foo', 'bar']), set(['42']))
            return

        if state == 'error':
            self.api.connectFail(ConnectError())
            return

        # Connecting the API causes a transition to state 'connected'
        self.api.connected()
        if state == 'connected':
            return

        # Setting filters while connected drops the connection
        self.monitor.setFilters(set(['foo', 'bar']), set(['42']))
        if state == 'disconnecting':
            return

        # Actually lose the connection
        self.api.protocol.connectionLost(failure.Failure(ResponseDone()))
        if state == 'disconnected':
            return

        # When disconnected, the next state is usually 'waiting'
        self.clock.advance(0)
        if state == 'waiting':
            return


    def setFilters(self, *args, **kwargs):
        self.patch(self.monitor, 'connect', self.connect)
        self.monitor.setFilters(*args, **kwargs)


    def connect(self, forceReconnect=False):
        self.connects = forceReconnect


    def test_init(self):
        """
        Set up monitor without passing a custom reactor.
        """
        self.monitor = twitter.TwitterMonitor(self.api, consumer=self)


    def test_initialStateStopped(self):
        """
        When the service has not been started, the state is 'stopped'.
        """
        self.setUpState('stopped')

        self.assertEqual(0, len(self.api.filterCalls))


    def test_unknownState(self):
        """
        Cannot transition to an unknown state.
        """
        self.assertRaises(ValueError, self.monitor.toState, "unknown")


    def test_setFilters(self):
        self.monitor.setFilters(set(['foo', 'bar']), set(['42']))
        self.assertEqual(set(['foo', 'bar']), self.monitor.terms)
        self.assertEqual(set(['42']), self.monitor.userIDs)


    def test_setFiltersStopped(self):
        """
        Setting filters when the service is not running, causes no connect.
        """
        self.setUpState('stopped')

        self.setFilters(set(['foo', 'bar']), set(['42']))
        self.assertIdentical(None, self.connects)


    def test_setFiltersIdle(self):
        """
        Setting filters in the idle state causes a connection attempt.
        """
        self.setUpState('idle')

        self.setFilters(set(['foo', 'bar']), set(['42']))
        self.assertFalse(self.connects)

        # Wait for delayed calls
        self.clock.advance(0)


    def test_setFiltersConnected(self):
        """
        Setting filters when connected causes disconnect and reconnect.
        """
        self.setUpState('connected')

        # Set filters to cause reconnect.
        self.setFilters(set(['foo', 'bar']), set(['42']))

        self.assertTrue(self.connects)

        # Wait for delayed calls
        self.clock.advance(0)


    def test_setFiltersConnecting(self):
        """
        Setting filters when connected causes disconnect and reconnect.
        """
        self.setUpState('connecting')

        # Set filter to cause reconnect.
        self.setFilters(set(['foo', 'bar']), set(['42']))

        self.assertTrue(self.connects)

        # Wait for delayed calls
        self.clock.advance(0)


    def test_setFiltersDisconnecting(self):
        """
        Setting filters when disconnecting should do nothing, wait for reconnect.
        """
        self.setUpState('disconnecting')

        # Set filters
        self.setFilters(set(['foo', 'bar']), set(['42']))

        self.assertIdentical(None, self.connects)

        # Wait for delayed calls
        self.clock.advance(0)


    def test_setFiltersDisconnected(self):
        """
        Setting filters when disconnected should do nothing, wait for reconnect.
        """
        self.setUpState('disconnected')

        # Set filters
        self.setFilters(set(['foo', 'bar']), set(['42']))

        self.assertIdentical(None, self.connects)

        # Wait for delayed calls
        self.clock.advance(0)
        self.clock.advance(5)


    def test_setFiltersWaiting(self):
        """
        Setting filters when waiting for reconnect should wait that out.
        """
        self.setUpState('waiting')

        # Set filters
        self.setFilters(set(['foo', 'bar']), set(['42']))

        self.assertIdentical(None, self.connects)

        # Wait for delayed calls
        self.clock.advance(0)
        self.clock.advance(5)


    def test_setFiltersAborting(self):
        """
        Setting filters when aborting the current connection awaits reconnect.
        """
        self.setUpState('aborting')

        # Set filters
        self.setFilters(set(['foo', 'bar']), set(['42']))

        self.assertIdentical(None, self.connects)

        # Wait for delayed calls
        self.clock.advance(0)


    def test_setFiltersError(self):
        """
        Setting filters when connecting fails waits for reconnect
        """
        self.setUpState('error')

        # Set filters.
        self.setFilters(set(['foo', 'bar']), set(['42']))

        self.assertIdentical(None, self.connects)

        # Wait for delayed calls
        self.clock.advance(0)
        self.flushLoggedErrors(ConnectError)
        self.clock.advance(0.25)



    def test_startServiceNoFilters(self):
        """
        When the service is started without filters, go to 'idle'.
        """
        self.monitor.startService()
        self.clock.advance(0)
        self.assertEqual(0, len(self.api.filterCalls))


    def test_startServiceWithFilters(self):
        """
        When the service is started with filters, initiate connection.
        """
        self.monitor.terms = set(['foo', 'bar'])
        self.monitor.startService()
        self.clock.advance(0)
        self.assertEqual(1, len(self.api.filterCalls))


    def test_stopServiceConnected(self):
        """
        Stopping the service while waiting to reconnect should abort.
        """
        self.setUpState('connected')

        # Stop the service.
        self.monitor.stopService()

        # Actually lose the connection
        self.api.protocol.connectionLost(failure.Failure(ResponseDone()))

        # No reconnect should be attempted.
        self.clock.advance(DELAY_INITIAL)
        self.assertEqual(1, len(self.api.filterCalls))
        self.assertIdentical(None, self.monitor.reconnectDelayedCall)


    def test_stopServiceWaiting(self):
        """
        Stopping the service while waiting to reconnect should abort.
        """
        self.setUpState('waiting')

        # Stop the service.
        self.monitor.stopService()

        # No reconnect should be attempted.
        self.clock.advance(DELAY_INITIAL)
        self.assertEqual(1, len(self.api.filterCalls))


    def test_stopServiceWaitingAndStarting(self):
        """
        Stopping and starting service while waiting, should cause 1 connect.
        """
        self.setUpState('waiting')

        # Stop the service.
        self.monitor.stopService()

        # Start the service before the initial reconnect delay expires
        self.clock.advance(DELAY_INITIAL - 1)
        self.monitor.startService()
        self.clock.advance(0)
        self.assertEqual(2, len(self.api.filterCalls))

        # After the initial reconnect delay, don't connect again!
        self.clock.advance(1)
        self.assertEqual(2, len(self.api.filterCalls), 'Extra connect')


    def test_stopServiceAfterReconnect(self):
        """
        Stopping the service after waiting is fine.
        """
        self.setUpState('waiting')

        # No reconnect should be attempted.
        self.clock.advance(DELAY_INITIAL)
        self.assertEqual(2, len(self.api.filterCalls))

        # Stop the service.
        self.monitor.stopService()
        self.clock.advance(0)


    def test_connectStopped(self):
        """
        Attempting to connect while the service is not running should fail.

        The initial state is stopped, so don't connect.
        """
        self.setUpState('stopped')

        self.assertFalse(self.monitor.connect())

        self.clock.advance(0)
        self.assertEqual(0, len(self.api.filterCalls))


    def test_connectIdle(self):
        """
        Attempting to connect while idle should succeed.

        The initial state is stopped, so don't connect.
        """
        self.setUpState('idle')

        self.monitor.terms = set(['foo', 'bar'])
        self.assertTrue(self.monitor.connect())
        self.clock.advance(0)

        self.assertEqual(1, len(self.api.filterCalls))


    def test_connectConnecting(self):
        """
        Don't connect while connecting.
        """
        self.setUpState('connecting')

        # Try to connect.
        self.assertFalse(self.monitor.connect())
        self.clock.advance(0)
        self.assertEqual(1, len(self.api.filterCalls), 'Extra connect')


    def test_connectConnectingReconnect(self):
        """
        Don't connect while connecting.
        """
        self.setUpState('connecting')

        # Try to connect.
        self.assertTrue(self.monitor.connect(forceReconnect=True))

        # As we haven't connected yet, we cannot drop the connection yet,
        # and no reconnect should have taken place.
        self.clock.advance(DELAY_INITIAL)
        self.assertEqual(1, len(self.api.filterCalls))

        # The initial connection is now established.
        self.api.connected()

        # A disconnect occurs right away.
        self.clock.advance(0)
        self.assertTrue(self.api.protocol.stopCalled)
        self.api.protocol.connectionLost(failure.Failure(ResponseDone()))
        self.clock.advance(0)

        # Now the reconnect occurs, wait for delayed calls.
        self.clock.advance(DELAY_INITIAL)
        self.assertEqual(2, len(self.api.filterCalls))


    def test_connectConnected(self):
        """
        Don't connect while connecting.
        """
        self.setUpState('connected')

        # Try to connect.
        self.assertFalse(self.monitor.connect())
        self.clock.advance(0)
        self.assertEqual(1, len(self.api.filterCalls), 'Extra connect')


    def test_connectConnectedReconnect(self):
        """
        Reconnect while connected.
        """
        self.setUpState('connected')

        # Try to connect.
        self.assertTrue(self.monitor.connect(forceReconnect=True))

        # As we haven't connected yet, we cannot drop the connection yet,
        # and no reconnect should have taken place.
        self.clock.advance(DELAY_INITIAL)
        self.assertEqual(1, len(self.api.filterCalls))

        # A disconnect occurs right away.
        self.clock.advance(0)
        self.assertTrue(self.api.protocol.stopCalled)
        self.api.protocol.connectionLost(failure.Failure(ResponseDone()))
        self.clock.advance(0)

        # Now the reconnect occurs, wait for delayed calls.
        self.clock.advance(DELAY_INITIAL)
        self.assertEqual(2, len(self.api.filterCalls))



    def test_connectDisconnected(self):
        """
        Connect immediately if disconnected.
        """
        self.setUpState('disconnected')

        # Try to connect.
        self.assertTrue(self.monitor.connect())
        self.clock.advance(0)
        self.assertEqual(2, len(self.api.filterCalls), 'Missing connect')

        # Now the reconnect occurs, wait for delayed calls.
        self.clock.advance(DELAY_INITIAL)
        self.assertEqual(2, len(self.api.filterCalls), 'Extra connect')


    def test_connectDisconnectedNoConsumer(self):
        """
        Don't connect without consumer if disconnected.
        """
        self.setUpState('disconnected')

        # Try to connect.
        self.monitor.consumer = None
        self.assertFalse(self.monitor.connect())
        self.clock.advance(0)

        self.assertEqual(1, len(self.api.filterCalls), 'Extra connect')


    def test_connectDisconnectedNoTerms(self):
        """
        Don't connect without terms or userIDs if disconnected.
        """
        self.setUpState('disconnected')

        # Try to connect.
        self.monitor.terms = set()
        self.monitor.userIDs = set()
        self.assertFalse(self.monitor.connect())
        self.clock.advance(0)

        self.assertEqual(1, len(self.api.filterCalls), 'Extra connect')


    def test_connectDisconnectedImmediately(self):
        """
        Connect immediately if delay is 0.
        """
        import copy
        self.monitor.backOffs = copy.deepcopy(self.monitor.backOffs)
        self.monitor.backOffs[None]['initial'] = 0
        self.setUpState('waiting')

        self.assertEqual(2, len(self.api.filterCalls), 'Missing connect')


    def test_connectAborting(self):
        """
        Don't connect while aborting.
        """
        self.setUpState('aborting')

        # Try to connect.
        self.assertFalse(self.monitor.connect())
        self.clock.advance(0)

        self.assertEqual(1, len(self.api.filterCalls), 'Extra connect')


    def test_connectDisconnecting(self):
        """
        Don't connect while disconnecting.
        """
        self.setUpState('disconnecting')

        # The stream is being disconnected, cannot connect explicitly
        self.assertFalse(self.monitor.connect())
        self.clock.advance(0)
        self.assertEqual(1, len(self.api.filterCalls), 'Extra connect')

        # Lose the connection.
        self.api.protocol.connectionLost(failure.Failure(ResponseDone()))
        self.clock.advance(0)

        # Now the reconnect occurs, wait for delayed calls.
        self.clock.advance(DELAY_INITIAL)
        self.assertEqual(2, len(self.api.filterCalls))


    def test_connectWaiting(self):
        """
        Setting filters when connected causes disconnect and reconnect.
        """
        self.setUpState('waiting')

        # Waiting for reconnect, cannot connect explicitly
        self.assertTrue(self.monitor.connect())
        self.clock.advance(0)
        self.assertEqual(2, len(self.api.filterCalls), 'Missing connect')

        # Now a reconnect should not occur, wait for erroneous delayed calls.
        self.clock.advance(DELAY_INITIAL)
        self.assertEqual(2, len(self.api.filterCalls), 'Extra connect')


    def test_connectConnectError(self):
        """
        Connect errors cause reconnects after a delay with back-offs.
        """
        self.setUpState('connecting')

        callCount = 1
        for delay in (0.25, 0.5, 1, 2, 4, 8, 16, 16):
            # Fail the connection attempt with a ConnectError
            self.api.connectFail(ConnectError())
            self.clock.advance(0)

            # The error is logged
            self.assertEquals(1, len(self.flushLoggedErrors(ConnectError)))

            # A reconnect is done after the delay
            self.clock.advance(delay)
            callCount += 1
            self.assertEqual(callCount, len(self.api.filterCalls))


    def test_connectHTTPError(self):
        """
        HTTP errors cause reconnects after a delay with back-offs.
        """
        self.setUpState('connecting')

        callCount = 1
        for delay in (10, 20, 40, 80, 160, 240, 240):
            # Fail the connection attempt with a ConnectError
            self.api.connectFail(http_error.Error(401))
            self.clock.advance(0)

            # The error is logged
            self.assertEquals(1, len(self.flushLoggedErrors(http_error.Error)))

            # A reconnect is done after the delay
            self.clock.advance(delay)
            callCount += 1
            self.assertEqual(callCount, len(self.api.filterCalls))


    def test_connectUnknownError(self):
        """
        Unknown errors while connecting are logged, transition to idle state.
        """
        self.setUpState('connecting')

        class UnknownError(Exception):
            pass

        callCount = 1
        for delay in (10, 20, 40, 80, 160, 240, 240):
            # Fail the connection attempt with a ConnectError
            self.api.connectFail(UnknownError())
            self.clock.advance(0)

            # The error is logged
            self.assertEquals(1, len(self.flushLoggedErrors(UnknownError)))

            # A reconnect is done after the delay
            self.clock.advance(delay)
            callCount += 1
            self.assertEqual(callCount, len(self.api.filterCalls))


    def test_connectionLostDone(self):
        """
        When the connection is closed while connected, attempt reconnect
        """
        self.setUpState('connected')

        # Connection closed by other party.
        self.api.protocol.connectionLost(failure.Failure(ResponseDone()))
        self.clock.advance(0)

        # A reconnect is attempted, but not before the back off delay.
        self.assertEqual(1, len(self.api.filterCalls))
        self.clock.advance(1)
        self.assertEqual(1, len(self.api.filterCalls))
        self.clock.advance(DELAY_INITIAL - 1)
        self.assertEqual(2, len(self.api.filterCalls))


    def test_connectionLostFailure(self):
        """
        When the connection is closed while connected, attempt reconnect
        """
        self.setUpState('connected')

        class Error(Exception):
            pass

        # Connection closed by other party.
        self.api.protocol.connectionLost(failure.Failure(Error()))
        self.clock.advance(0)

        # A reconnect is attempted, but not before the back off delay.
        self.assertEqual(1, len(self.api.filterCalls))
        self.clock.advance(1)
        self.assertEqual(1, len(self.api.filterCalls))
        self.clock.advance(self.monitor.backOffs['other']['initial'] - 1)
        self.assertEqual(2, len(self.api.filterCalls))

        self.assertEqual(1, len(self.flushLoggedErrors(Error)))
