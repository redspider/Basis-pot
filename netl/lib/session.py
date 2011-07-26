"""

Session management

This session implementation utilises a MongoDB backend to provide the following:

1. Authenticity
    All session data is stored server-side, clients receive a 256bit randomly generated token using the URL-safe
    Base64 encoding alphabet as their session ID.

2. Revocation
    Sessions can be revoked (expired) on an individual basis via .expire(), or as a group via .expire_set() in
    order to kill all sessions relating to a particular user (necessary for credentials changes)

3. Upgrades
    When a session crosses a permissions boundary (Login, Administration, HTTPS), the .rotate() method can be called to
    expire the old session ID and move the data into a new one.

4. Idle detection
    When a session has been idle for session.timeout seconds it is expired automatically.

5. Secure by default
    Where possible, the interface offers secure defaults and provides an API that makes it clear what methods should
    be called where in your code in order to operate securely.

Configuration

session.domain          Domain name to limit session to
session.path            Path to limit session to
session.timeout         Session idle timeout (Recommend no more than 20 minutes, probably 10)
session.secure_only     True if you want HTTPS only
session.csrf_lifetime   Lifetime (in seconds) of any given CSRF token. Recommend 10 minutes
session.lifetime        Lifetime of any single session ID before it is auto-rotated
session.mongodb_url     MongoDB url
session.mongodb_db      MongoDB database


Scenario usage

Storing data

def foo(request):
    request.session['name'] = 'phi'

Retrieving data

def foo(request):
    name = request.session.get('name',None)

Logout

def logout(request):
    request.session.expire()
    request.session.reset()

Password change (must expire all other sessions for this user since they no longer have valid credentials)

def set_password(request):
    # ... save password to database etc
    actor_id = request.session['actor_id']
    request.session.expire_set({'actor_id': actor_id})
    request.session.rotate()

Credentials upgrade (or moving to HTTPS)

def login():
    # ... check user/pass as given etc here
    request.session.rotate()
    request.session['actor_id'] = actor_id

Protected form generation.

def get_form(request):
    csrf_token = request.session.create_csrf_token('https.login_form')
    # ... render form etc

def post_form(request):
    csrf_token = request.params.get('csrf_token')
    try:
        request.session.consume_csrf_token(csrf_token,'https.login_form')
    except InvalidCSRFToken:
        # Send user back to the form to re-enter data
        return

    # go ahead with form stuff


Notes

The CSRF approach can be replaced with a non-stored method, utilising the _csrf_id directly and signing it with the
key and a timestamp. General opinion seems to be that the one-shot stored token method offers no useful security
features above this.

"""
from datetime import datetime, timedelta
import logging
import pymongo
from netl.lib.token import create_token, valid_token

config = {}
mongodb = None

logging.basicConfig()
log = logging.getLogger(__file__)
log.setLevel(logging.DEBUG)

class InvalidCSRFToken(Exception):
    pass

class Session(dict):
    id = None # Session ID
    modified = None # Has the session data been modified?
    expired = None # Is the session expired?
    _store = None # Rotation-independent ID to tie to CSRF tokens
    _csrf_id = None

    def __init__(self, request):
        dict.__init__(self)

        self.request = request
        self.modified = False
        self.expired = False

        self._store = mongodb[config['mongodb_db']]
        
        self.id = str(request.str_cookies.get(config['name'], None))

        # Did we find a session ID in the cookie?
        if not self.id:
            log.debug("No session token found in cookie")
            self.reset()
            return

        # Is the token valid?
        if not valid_token(self.id):
            log.warn("Invalid session token found in cookie")
            self.reset()
            return

        doc = self._store.session.find_one({'session_id': self.id})

        # Did we find the session ID in the store?
        if not doc:
            log.debug("No session matches provided token in store")
            self.reset()
            return

        # Has this session been forcibly expired?
        self.last_update = doc['last_update']
        if doc.get('expired',False):
            log.warn("Attempt to use expired session")
            self.reset()
            return

        # Is this session idle too long?
        age = datetime.now() - self.last_update
        age_seconds = age.days * (24*60*60) + age.seconds
        if age_seconds > config['timeout']:
            log.debug("Session idle too long")
            self.expire()
            self.reset()
            return

        # Map the data into the dictionary
        for k in doc['data'].keys():
            self[k] = doc['data'][k]

        self._csrf_id = doc['csrf_id']

        self.modified = False

    def reset(self):
        """
        Reset the session. Creates a new token, wipes any existing data.

        This does NOT expire the previous session ID (if there was one). To do this, call expire() first.
        """
        self.id = create_token()
        log.debug("Generating new session %s" % self.id)
        
        self.modified = True
        self.expired = False
        self._csrf_id = create_token()
        self.last_update = datetime.now()
        self.clear()

    def __setitem__(self, k, value):
        self.modified = True
        return dict.__setitem__(self, k, value)

    def __delitem__(self, k):
        self.modified = True
        return dict.__delitem__(self, k)

    def expire(self):
        """
        Expires the session. The data is retained within the session object however no new requests will
        be able to retrieve it.
        """
        log.debug("Expiring session %s" % self.id)
        self._store.session.update({'session_id': self.id}, {'$set': {'expired': True}})
        self.expired = True

    def expire_set(self, match):
        """
        Expires a set of matching settings. For example,

        session.expire_set({'data.user_id': 55})
        """
        self._store.session.update(match, {'$set': {'expired': True}})
        self.expired = True

    def rotate(self):
        """
        Rotate the session. Expires the existing session ID then creates a new one, while retaining the existing
        data. Rotation of the session does not invalidate active CSRF tokens associated with the session.

        New session is not saved until the end of the request.
        """
        log.debug("Rotating session %s out" % self.id)

        # Expire current session
        if not self.expired:
            self.expire()

        # Create new session ID
        self.id = create_token()
        self.modified = True
        self.expired = False

    def save(self):
        """
        Save the current session information to store. Done automatically when the request completes.
        """
        if self.expired:
            log.debug("Not saving session %s - expired" % self.id)
            return
        
        log.debug("Saving session %s to store" % self.id)
        d = dict(self)

        self.last_update = datetime.now()
        self._store.session.update({'session_id': self.id}, {'$set': {
            'last_update': self.last_update,
            'session_id': self.id,
            'csrf_id': self._csrf_id,
            'data': dict(self)
            }}, upsert=True)

    def create_csrf_token(self, key=None):
        """
        Create a CSRF token, with an optional key (form name, page name, whatever)
        """
        token = create_token()
        self._store.csrf.insert({
            'token': token,
            'csrf_id': self._csrf_id,
            'key': key,
            'dated': datetime.now()
        })
        log.debug("Created new CSRF token %s" % token)
        return token

    def consume_csrf_token(self, token, key=None):
        """
        Attempt to consume a CSRF token. Will match session id, token and key and consume it if matched. If the
        match fails (no valid token) it will raise InvalidCSRFToken
        """
        if self.expired:
            log.warn("Attempt to consume CSRF token from expired session")
            raise InvalidCSRFToken()

        result = self._store.csrf.find_and_modify({'csrf_id': self._csrf_id, 'token': token, 'key': key, 'dated': {'$gt': datetime.now() - timedelta(seconds=config['csrf_lifetime'])}},remove=True)
        if not result:
            log.warn("Attempt to consume invalid CSRF token")
            raise InvalidCSRFToken()
        log.debug("Consumed CSRF token %s" % token)


def on_request(event):
    """
    Decorate request with session
    @param event:
    @return:
    """
    event.request.session = Session(event.request)

def on_response(event):
    """

    @param event:
    @return:
    """
    # TODO: rotate the session if it's old enough (timeout or possibly seen enough requests)

    event.request.session.save()

    # TODO: delete cookie if expired

    event.response.set_cookie(config['name'],
                              value=event.request.session.id,
                              path=config['path'],
                              domain=config['domain'],
                              secure=config['secure_only'],
                              httponly=True,
                              overwrite=True)

def init(settings):
    """
    Initialise session subsystem

    @param settings:dict Session configuration settings (see module docs)
    @return:
    """
    global mongodb

    config['domain'] = settings.get('session.domain', None)
    config['path'] = settings.get('session.path')
    config['name'] = settings.get('session.name')
    config['timeout'] = settings.get('session.timeout')
    config['secure_only'] = settings.get('session.secure_only')
    config['csrf_lifetime'] = settings.get('session.csrf_lifetime', 10*60)

    mongodb = pymongo.Connection(settings.get('session.mongodb_url'))
    config['mongodb_db'] = settings.get('session.mongodb_db')
