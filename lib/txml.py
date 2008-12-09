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
    tag_name = None

    def __init__(self):
        self.done = False
        self.current_ob = None
        for p in self.SIMPLE_PROPS:
            self.__dict__[p] = None

    def gotTagStart(self, name, attrs):
        if self.current_ob:
            self.current_ob.gotTagStart(name, attrs)
        elif name in self.COMPLEX_PROPS:
            self.current_ob = self.COMPLEX_PROPS[name]()
        elif name in self.SIMPLE_PROPS:
            pass
        else:
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
            self.__dict__[name] = data

    def __repr__(self):
        return "{%s %s}" % (self.tag_name, self.__dict__)

class Author(BaseXMLHandler):

    SIMPLE_PROPS = [ 'name', 'uri' ]
    tag_name = 'author'

class Entry(BaseXMLHandler):

    SIMPLE_PROPS = ['id', 'published', 'title', 'content', 'link']
    COMPLEX_PROPS = {'author': Author}

    tag_name = 'entry'

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
        'in_reply_to_status_id', 'in_reply_to_user_id', 'favorited']

class User(BaseXMLHandler):

    SIMPLE_PROPS = ['id', 'name', 'screen_name', 'location', 'description',
        'profile_image_url', 'url', 'protected', 'followers_count']
    COMPLEX_PROPS = {'status': Status}

class Parser(sux.XMLParser):

    toplevel_tag = 'entry'
    toplevel_type = None

    """A file-like thingy that parses a friendfeed feed with SUX."""
    def __init__(self, delegate):
        self.delegate=delegate

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
            self.currentEntry = self.toplevel_type()
        elif self.currentEntry:
            self.currentEntry.gotTagStart(name, attrs)

    def gotTagEnd(self, name):
        if name == self.toplevel_tag:
            self.currentEntry.done = True
            del self.currentEntry.current_ob
            self.delegate(self.currentEntry)
            self.currentEntry = None
        elif self.currentEntry:
            self.currentEntry.gotTagEnd(name, ''.join(self.data).decode('utf8'))

    def gotText(self, data):
        self.data.append(data)

    def gotEntityReference(self, data):
        e = {'quot': '"', 'lt': '&lt;', 'gt': '&gt;', 'amp': '&amp;'}
        if e.has_key(data):
            self.data.append(e[data])
        else:
            print "Unhandled entity reference: ", data

class Feed(Parser):

    toplevel_tag = 'entry'
    toplevel_type = Entry

class Users(Parser):

    toplevel_tag = 'user'
    toplevel_type = User

def parseXML(xml):
    return microdom.parseXMLString(xml)

def parseUpdateResponse(xml):
    return parseXML(xml).getElementsByTagName("id")[0].firstChild().data
