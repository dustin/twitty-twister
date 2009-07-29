from twisted.internet import error
from twisted.web import sux, microdom

class NoopParser(object):
    def __init__(self, n):
        self.name = n
        self.done = False
    def gotTagStart(self, name, attrs):
        pass
    def gotTagEnd(self, name, data):
        self.done = (name == self.name)

class BaseXMLHandler(object):

    SIMPLE_PROPS = []
    COMPLEX_PROPS = {}

    def __init__(self, n):
        self.done = False
        self.current_ob = None
        self.tag_name = n
        for p in self.SIMPLE_PROPS:
            self.__dict__[p] = None

    def gotTagStart(self, name, attrs):
        if self.current_ob:
            self.current_ob.gotTagStart(name, attrs)
        elif name in self.COMPLEX_PROPS:
            self.current_ob = self.COMPLEX_PROPS[name](name)
        elif name in self.SIMPLE_PROPS:
            pass
        else:
            print "Got unknown tag", name, "in", self.__class__
            self.current_ob = NoopParser(name)

    def gotTagEnd(self, name, data):
        if self.current_ob:
            self.current_ob.gotTagEnd(name, data)
            if self.current_ob.done:
                if name in self.COMPLEX_PROPS:
                    self.__dict__[name] = self.current_ob
                self.current_ob = None
        elif name == self.tag_name:
            self.done = True
            del self.current_ob
        elif name in self.SIMPLE_PROPS:
            self.__dict__[self.cleanup(name)] = data

    def cleanup(self, n):
        return n.replace(':', '_')

    def __repr__(self):
        return "{%s %s}" % (self.tag_name, self.__dict__)

class Author(BaseXMLHandler):

    SIMPLE_PROPS = [ 'name', 'uri' ]

class Entry(BaseXMLHandler):

    SIMPLE_PROPS = ['id', 'published', 'title', 'content', 'link', 'updated',
                    'twitter:source', 'twitter:lang']
    COMPLEX_PROPS = {'author': Author}

    def gotTagStart(self, name, attrs):
        super(Entry, self).gotTagStart(name, attrs)
        if name == 'link':
            self.__dict__[attrs['rel']] = attrs['href']

    def gotTagEnd(self, name, data):
        super(Entry, self).gotTagEnd(name, data)
        if name == 'link':
            del self.link

class Status(BaseXMLHandler):

    SIMPLE_PROPS = ['created_at', 'id', 'text', 'source', 'truncated',
        'in_reply_to_status_id', 'in_reply_to_screen_name',
        'in_reply_to_user_id', 'favorited']

class User(BaseXMLHandler):

    SIMPLE_PROPS = ['id', 'name', 'screen_name', 'location', 'description',
        'profile_image_url', 'url', 'protected', 'followers_count',
        'profile_background_color', 'profile_text_color', 'profile_link_color',
        'profile_sidebar_fill_color', 'profile_sidebar_border_color',
        'friends_count', 'created_at', 'favourites_count', 'utc_offset',
        'time_zone', 'following', 'notifications', 'statuses_count',
        'profile_background_image_url', 'profile_background_tile', 'verified']
    COMPLEX_PROPS = {'status': Status}

# Hack to patch this in...

Status.COMPLEX_PROPS = {'user': User}

class Parser(sux.XMLParser):

    toplevel_tag = 'entry'
    toplevel_type = None

    """A file-like thingy that parses a friendfeed feed with SUX."""
    def __init__(self, delegate, extra_args=None):
        self.delegate=delegate
        self.extra_args=extra_args

        self.connectionMade()
        self.currentEntry=None
        self.data=[]
    def write(self, b):
        self.dataReceived(b)
    def close(self):
        self.connectionLost(error.ConnectionDone())
    def open(self):
        pass
    def read(self):
        return None

    # XML Callbacks
    def gotTagStart(self, name, attrs):
        self.data=[]
        if name ==  self.toplevel_tag:
            self.currentEntry = self.toplevel_type(name)
        elif self.currentEntry:
            self.currentEntry.gotTagStart(name, attrs)

    def gotTagEnd(self, name):
        if name == self.toplevel_tag:
            self.currentEntry.done = True
            del self.currentEntry.current_ob
            if self.extra_args is None:
                self.delegate(self.currentEntry)
            else:
                self.delegate(self.currentEntry, self.extra_args)
            self.currentEntry = None
        elif self.currentEntry:
            self.currentEntry.gotTagEnd(name, ''.join(self.data).decode('utf8'))

    def gotText(self, data):
        self.data.append(data)

    def gotEntityReference(self, data):
        e = {'quot': '"', 'lt': '&lt;', 'gt': '&gt;', 'amp': '&amp;'}
        if e.has_key(data):
            self.data.append(e[data])
        elif data[0] == '#':
            self.data.append('&' + data + ';')
        else:
            print "Unhandled entity reference: ", data

class DirectMessage(BaseXMLHandler):

    SIMPLE_PROPS = ['id', 'sender_id', 'text', 'recipient_id', 'created_at',
        'sender_screen_name', 'recipient_screen_name']
    COMPLEX_PROPS = {'sender': User, 'recipient': User}

class Feed(Parser):

    toplevel_tag = 'entry'
    toplevel_type = Entry

class Users(Parser):

    toplevel_tag = 'user'
    toplevel_type = User

class Direct(Parser):

    toplevel_tag = 'direct_message'
    toplevel_type = DirectMessage

class StatusList(Parser):

    toplevel_tag = 'status'
    toplevel_type = Status

class HoseFeed(Parser):

    toplevel_tag = 'status'
    toplevel_type = Status

def parseXML(xml):
    return microdom.parseXMLString(xml)

def parseUpdateResponse(xml):
    return parseXML(xml).getElementsByTagName("id")[0].firstChild().data
