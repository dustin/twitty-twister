#!/usr/bin/env python
"""
Twisted Twitter interface.

Copyright (c) 2008  Dustin Sallings <dustin@spy.net>
Copyright (c) 2009  Kevin Dunglas <dunglas@gmail.com>
"""

import base64
import urllib
import mimetypes
import mimetools
import logging

from oauth import oauth

from twisted.internet import defer, reactor
from twisted.web import client

import txml

SIGNATURE_METHOD = oauth.OAuthSignatureMethod_HMAC_SHA1()

BASE_URL="http://twitter.com"
SEARCH_URL="http://search.twitter.com/search.atom"


logger = logging.getLogger('twittytwister.twitter')


##### ugly hack to work around a bug on HTTPDownloader on Twisted 8.2.0 (fixed on 9.0.0)
def install_twisted_fix():
    orig_method = client.HTTPDownloader.gotHeaders
    def gotHeaders(self, headers):
        client.HTTPClientFactory.gotHeaders(self, headers)
        orig_method(self, headers)
    client.HTTPDownloader.gotHeaders = gotHeaders

def buggy_twisted():
    o = client.HTTPDownloader('http://dummy-url/foo', None)
    client.HTTPDownloader.gotHeaders(o, {})
    if o.response_headers is None:
        return True
    return False

if buggy_twisted():
    install_twisted_fix()

##### end of hack


class TwitterClientInfo:
    def __init__ (self, name, version = None, url = None):
        self.name = name
        self.version = version
        self.url = url

    def get_headers (self):
        headers = [
                ('X-Twitter-Client',self.name),
                ('X-Twitter-Client-Version',self.version),
                ('X-Twitter-Client-URL',self.url),
                ]
        return dict(filter(lambda x: x[1] != None, headers))

    def get_source (self):
        return self.name


def downloadPage(url, file, **kwargs):
    """Start a HTTP download, returning a HTTPDownloader object"""

    # The Twisted API is weird:
    # 1) web.client.downloadPage() doesn't give us the HTTP headers
    # 2) there is no method that simply accepts a URL and gives you back
    #    a HTTPDownloader object

    #TODO: convert getPage() usage to something similar, too

    downloader = client.HTTPDownloader(url, file, **kwargs)
    if downloader.scheme == 'https':
        from twisted.internet import ssl
        contextFactory = ssl.ClientContextFactory()
        reactor.connectSSL(downloader.host, downloader.port,
                           downloader, contextFactory)
    else:
        reactor.connectTCP(downloader.host, downloader.port,
                           downloader)
    return downloader


class Twitter(object):

    agent="twitty twister"

    def __init__(self, user=None, passwd=None,
        base_url=BASE_URL, search_url=SEARCH_URL,
                 consumer=None, token=None, signature_method=SIGNATURE_METHOD,client_info = None):

        self.base_url = base_url
        self.search_url = search_url

        self.use_auth = False
        self.use_oauth = False
        self.client_info = None

        # rate-limit info:
        self.rate_limit_limit = None
        self.rate_limit_remaining = None
        self.rate_limit_reset = None

        if user and passwd:
            self.use_auth = True
            self.username = user
            self.password = passwd

        if consumer and token:
            self.use_auth = True
            self.use_oauth = True
            self.consumer = consumer
            self.token = token
            self.signature_method = signature_method

        if client_info != None:
            self.client_info = client_info


    def __makeOAuthHeader(self, method, url, parameters={}, headers={}):
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(self.consumer,
            token=self.token, http_method=method, http_url=url, parameters=parameters)
        oauth_request.sign_request(self.signature_method, self.consumer, self.token)

        headers.update(oauth_request.to_header())
        return headers

    def __makeAuthHeader(self, headers={}):
        authorization = base64.encodestring('%s:%s'
            % (self.username, self.password))[:-1]
        headers['Authorization'] = "Basic %s" % authorization
        return headers

    def _makeAuthHeader(self, method, url, parameters={}, headers={}):
        if self.use_oauth:
            return self.__makeOAuthHeader(method, url, parameters, headers)
        else:
            return self.__makeAuthHeader(headers)

    def makeAuthHeader(self, method, url, parameters={}, headers={}):
        if self.use_auth:
            return self._makeAuthHeader(method, url, parameters, headers)
        else:
            return headers

    def _urlencode(self, h):
        rv = []
        for k,v in h.iteritems():
            rv.append('%s=%s' %
                (urllib.quote(k.encode("utf-8")),
                urllib.quote(v.encode("utf-8"))))
        return '&'.join(rv)

    def __encodeMultipart(self, fields, files):
        """
        fields is a sequence of (name, value) elements for regular form fields.
        files is a sequence of (name, filename, value) elements for data to be uploaded as files
        Return (content_type, body) ready for httplib.HTTP instance
        """
        boundary = mimetools.choose_boundary()
        crlf = '\r\n'

        l = []
        for k, v in fields:
            l.append('--' + boundary)
            l.append('Content-Disposition: form-data; name="%s"' % k)
            l.append('')
            l.append(v)
        for (k, f, v) in files:
            l.append('--' + boundary)
            l.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (k, f))
            l.append('Content-Type: %s' % self.__getContentType(f))
            l.append('')
            l.append(v)
        l.append('--' + boundary + '--')
        l.append('')
        body = crlf.join(l)

        return boundary, body

    def gotHeaders(self, headers):
        logger.debug("hdrs: %r", headers)

        def ih(hdr):
            r = headers.get(hdr)
            if r is not None and len(r) > 0 and r[0]:
                return int(r[0])
            else:
                return None

        self.rate_limit_limit = ih('x-ratelimit-limit')
        self.rate_limit_remaining = ih('x-ratelimit-remaining')
        self.rate_limit_reset = ih('x-ratelimit-reset')

        logger.debug('hdrs end')


    def __getContentType(self, filename):
        return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

    def __postMultipart(self, path, fields=(), files=()):
        url = self.base_url + path

        (boundary, body) = self.__encodeMultipart(fields, files)
        headers = {'Content-Type': 'multipart/form-data; boundary=%s' % boundary,
            'Content-Length': str(len(body))
            }

        self._makeAuthHeader('POST', url, headers=headers)

        return client.getPage(url, method='POST',
            agent=self.agent,
            postdata=body, headers=headers)

    #TODO: deprecate __post()?
    def __post(self, path, args={}):
        headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'}

        url = self.base_url + path

        self._makeAuthHeader('POST', url, args, headers)

        if self.client_info != None:
            headers.update(self.client_info.get_headers())
            args['source'] = self.client_info.get_source()

        return client.getPage(url, method='POST',
            agent=self.agent,
            postdata=self._urlencode(args), headers=headers)

    def __doDownloadPage(self, *args, **kwargs):
        """Works like client.downloadPage(), but handle incoming headers
        """
        logger.debug("download page: %r, %r" % (args, kwargs))

        d = defer.Deferred()
        c = downloadPage(*args, **kwargs)

        def done(*args, **kwargs):
            self.gotHeaders(c.response_headers)
            return d.callback(*args, **kwargs)

        c.deferred.addCallbacks(done, d.errback)
        return d

    def __postPage(self, path, parser, args={}, params=None):
        url = self.base_url + path
        if params:
            url += '?' + self._urlencode(params)

        headers = self.makeAuthHeader('GET', url)

        if self.client_info != None:
            headers.update(self.client_info.get_headers())
            args['source'] = self.client_info.get_source()

        return self.__doDownloadPage(url, parser, method='POST',
            agent=self.agent,
            postdata=self._urlencode(args), headers=headers)

    def __downloadPage(self, path, parser, params=None):
        url = self.base_url + path
        if params:
            url += '?' + self._urlencode(params)

        headers = self.makeAuthHeader('GET', url)

        return self.__doDownloadPage(url, parser,
            agent=self.agent, headers=headers)

    def __get(self, path, delegate, params, parser_factory=txml.Feed, extra_args=None):
        parser = parser_factory(delegate, extra_args)
        return self.__downloadPage(path, parser, params)

    def verify_credentials(self, delegate=None):
        "Verify a user's credentials."
        parser = txml.Users(delegate)
        return self.__downloadPage('/account/verify_credentials.xml', parser)

    def __parsed_post(self, hdef, parser):
        deferred = defer.Deferred()
        hdef.addErrback(lambda e: deferred.errback(e))
        hdef.addCallback(lambda p: deferred.callback(parser(p)))
        return deferred

    def update(self, status, source=None):
        "Update your status.  Returns the ID of the new post."
        params={'status': status}
        if source:
            params['source'] = source
        return self.__parsed_post(self.__post('/statuses/update.xml', params),
            txml.parseUpdateResponse)

    def friends(self, delegate, params={}, extra_args=None):
        """Get updates from friends.

        Calls the delgate once for each status object received."""
        return self.__get('/statuses/friends_timeline.xml', delegate, params,
            txml.Statuses, extra_args=extra_args)

    def home_timeline(self, delegate, params={}, extra_args=None):
        """Get updates from friends.

        Calls the delgate once for each status object received."""
        return self.__get('/statuses/home_timeline.xml', delegate, params,
            txml.Statuses, extra_args=extra_args)

    def user_timeline(self, delegate, user=None, params={}, extra_args=None):
        """Get the most recent updates for a user.

        If no user is specified, the statuses for the authenticating user are
        returned.

        See search for example of how results are returned."""
        if user:
            params['id'] = user
        return self.__get('/statuses/user_timeline.xml', delegate, params,
                          txml.Statuses, extra_args=extra_args)

    def public_timeline(self, delegate, params={}, extra_args=None):
        "Get the most recent public timeline."

        return self.__get('/statuses/public_timeline.atom', delegate, params,
                          extra_args=extra_args)

    def direct_messages(self, delegate, params={}, extra_args=None):
        """Get direct messages for the authenticating user.

        Search results are returned one message at a time a DirectMessage
        objects"""
        return self.__get('/direct_messages.xml', delegate, params,
                          txml.Direct, extra_args=extra_args)

    def replies(self, delegate, params={}, extra_args=None):
        """Get the most recent replies for the authenticating user.

        See search for example of how results are returned."""
        return self.__get('/statuses/replies.atom', delegate, params,
                          extra_args=extra_args)

    def follow(self, user):
        """Follow the given user.

        Returns no useful data."""
        return self.__post('/friendships/create/%s.xml' % user)

    def leave(self, user):
        """Stop following the given user.

        Returns no useful data."""
        return self.__post('/friendships/destroy/%s.xml' % user)

    def follow_user(self, user, delegate):
        """Follow the given user.

        Returns the user info back to the given delegate
        """
        parser = txml.Users(delegate)
        return self.__postPage('/friendships/create/%s.xml' % (user), parser)

    def unfollow_user(self, user, delegate):
        """Unfollow the given user.

        Returns the user info back to the given delegate
        """
        parser = txml.Users(delegate)
        return self.__postPage('/friendships/destroy/%s.xml' % (user), parser)

    def __paging_get(self, url, delegate, params, pager, page_delegate=None):
        def end_page(p):
            if page_delegate:
                page_delegate(p.next_cursor, p.previous_cursor)

        parser = pager.pagingParser(delegate, page_delegate=end_page)
        return self.__downloadPage(url, parser, params)

    def __nopaging_get(self, url, delegate, params, pager):
        parser = pager.noPagingParser(delegate)
        return self.__downloadPage(url, parser, params)

    def __get_maybe_paging(self, url, delegate, params, pager, extra_args=None, page_delegate=None):
        if extra_args is None:
            eargs = ()
        else:
            eargs = (extra_args,)

        def do_delegate(i):
            delegate(i, *eargs)

        if params.has_key('cursor'):
            return self.__paging_get(url, delegate, params, pager, page_delegate)
        else:
            return self.__nopaging_get(url, delegate, params, pager)


    def list_friends(self, delegate, user=None, params={}, extra_args=None, page_delegate=None):
        """Get the list of friends for a user.

        Calls the delegate with each user object found."""
        if user:
            url = '/statuses/friends/' + user + '.xml'
        else:
            url = '/statuses/friends.xml'

        return self.__get_maybe_paging(url, delegate, params, txml.PagedUserList, extra_args, page_delegate)

    def list_followers(self, delegate, user=None, params=None, extra_args=None, page_delegate=None):
        """Get the list of followers for a user.

        Calls the delegate with each user object found."""
        if user:
            url = '/statuses/followers/' + user + '.xml'
        else:
            url = '/statuses/followers.xml'

        return self.__get_maybe_paging(url, delegate, params, txml.PagedUserList, extra_args, page_delegate)

    def friends_ids(self, delegate, user, params={}, extra_args=None, page_delegate=None):
        return self.__get_maybe_paging('/friends/ids/%s.xml' % (user), delegate, params, txml.PagedIDList, extra_args, page_delegate)

    def followers_ids(self, delegate, user, params={}, extra_args=None, page_delegate=None):
        return self.__get_maybe_paging('/followers/ids/%s.xml' % (user), delegate, params, txml.PagedIDList, extra_args, page_delegate)


    def show_user(self, user):
        """Get the info for a specific user.

        Returns a delegate that will receive the user in a callback."""

        url = '/users/show/%s.xml' % (user)
        d = defer.Deferred()

        self.__downloadPage(url, txml.Users(lambda u: d.callback(u))) \
            .addErrback(lambda e: d.errback(e))

        return d

    def search(self, query, delegate, args=None, extra_args=None):
        """Perform a search query.

        Results are given one at a time to the delegate.  An example delegate
        may look like this:

        def exampleDelegate(entry):
            print entry.title"""
        if args is None:
            args = {}
        args['q'] = query
        return self.__doDownloadPage(self.search_url + '?' + self._urlencode(args),
            txml.Feed(delegate, extra_args), agent=self.agent)

    def block(self, user):
        """Block the given user.

        Returns no useful data."""
        return self.__post('/blocks/create/%s.xml' % user)

    def unblock(self, user):
        """Unblock the given user.

        Returns no useful data."""
        return self.__post('/blocks/destroy/%s.xml' % user)

    def update_profile_image(self, filename, image):
        """Update the profile image of an authenticated user.
        The image parameter must be raw data.

        Returns no useful data."""

        return self.__postMultipart('/account/update_profile_image.xml',
                                    files=(('image', filename, image),))

class TwitterFeed(Twitter):
    """
    Realtime feed handling class.

    Results are given one at a time to the delegate. An example delegate
    may look like this::

        def exampleDelegate(entry):
            print entry.text
    """

    def _rtfeed(self, url, delegate, args):
        if args:
            url += '?' + self._urlencode(args)
        print 'Fetching', url
        return client.downloadPage(url, txml.HoseFeed(delegate), agent=self.agent,
                                   headers=self.__makeAuthHeader())


    def sample(self, delegate, args=None):
        """
        Returns a random sample of all public statuses.

        The actual access level determines the portion of the firehose.
        """
        return self._rtfeed('http://stream.twitter.com/1/statuses/sample.xml',
                            delegate,
                            args)


    def spritzer(self, delegate, args=None):
        """
        Get the spritzer feed.

        The API method 'spritzer' is deprecated. This method is provided for
        backwards compatibility. Use L{sample} instead.
        """
        return self.sample(delegate, args)


    def gardenhose(self, delegate, args=None):
        """
        Get the gardenhose feed.

        The API method 'gardenhose' is deprecated. This method is provided for
        backwards compatibility. Use L{sample} instead.
        """
        return self.sample(delegate, args=None)


    def firehose(self, delegate, args=None):
        """
        Returns all public statuses.
        """
        return self._rtfeed('http://stream.twitter.com/1/statuses/firehose.xml',
                            delegate,
                            args)


    def filter(self, delegate, args=None):
        """
        Returns public statuses that match one or more filter predicates.
        """
        return self._rtfeed('http://stream.twitter.com/1/statuses/filter.xml',
                            delegate,
                            args)


    def follow(self, delegate, follow):
        """
        Returns public statuses from or in reply to a set of users.

        Note that the old API method 'follow' is deprecated. This method
        is backwards compatible and provides a shorthand to L{filter}. The
        actual allowed number of user IDs depends on the access level of the
        used account.
        """
        return self.filter(delegate, {'follow': ','.join(follow)})


    def birddog(self, delegate, follow):
        """
        Follow up to 200,000 users in realtime.

        The API method `birddog` is deprecated. This method is provided for
        backwards compatibility. Use L{follow} or L{filter} instead.
        """
        return self.follow(delegate, follow)


    def shadow(self, delegate, follow):
        """
        Follow up to 2,000 users in realtime.

        The API method `birddog` is deprecated. This method is provided for
        backwards compatibility. Use L{follow} or L{filter} instead.
        """
        return self.follow(delegate, follow, 'shadow')


    def track(self, delegate, terms):
        """
        Returns public statuses matching a set of keywords.

        Note that the old API method 'follow' is deprecated. This method is
        backwards compatible and provides a shorthand to L{filter}. The actual
        allowed number of keywords in C{terms} depends on the access level of
        the used account.
        """
        return self.filter(delegate, {'track': ','.join(terms)})

# vim: set expandtab:
