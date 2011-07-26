"""

Identity management

Scenario usage:

Logging in

def login(request):
    # ... verify username/password or whatever
    request.identity.set(real_id, actor_id)

Retrieving actor

def display_name(request):
    if not request.identity.is_set():
        return HTTPForbidden("No idea who you are?")
        
    user = model.user.get(request.identity.id)
    # .. display user or whatever

Switching identities

def su(request)
    switch_to = request.params.get('switch_to')
    if not model.user.can_switch_to(request.identity.real_id, switch_to):
        return HTTPForbidden("No authority to switch")
    request.identity.act_as(request.params.get('switch_to')
    # .. display confirmation

Changed password

def set_password(request)
    # .. set password etc
    request.identity.changed_credentials()

Logging out (this session only)

def logout(request):
    request.identity.logout()


Logging out (all sessions for this user)

def logout_all(request):
    request.identity.logout_all()

"""
import logging


logging.basicConfig()
log = logging.getLogger(__file__)
log.setLevel(logging.DEBUG)


class Identity(object):
    request = None
    real_id = None
    id = None

    def __init__(self, request):
        """
        Initialise identity

        @param request:
        @return:
        """
        self.request = request
        self.real_id = request.session.get('real_id', None)
        self.id = request.session.get('actor_id', None)
        log.debug("Identity initialised with %s (real), %s (actor)" % (self.real_id, self.id))

    def set(self, real_id, actor_id):
        """
        Set real and actor ID. Should be called on login

        @param real_id:
        @param actor_id:
        @return:
        """
        assert real_id, "Attempt to set identity to a null real ID"
        assert actor_id, "Attempt to set identity to a null actor ID"

        self.real_id = real_id
        self.id = actor_id
        self.request.session['real_id'] = real_id
        self.request.session['actor_id'] = actor_id

        self.request.session.rotate()
        log.debug("Set identity as %s (real), %s (actor)" % (self.real_id, self.id))

    def is_set(self):
        """
        Check whether there's a valid ID
        
        @return:
        """
        return bool(self.real_id)

    def act_as(self, actor_id):
        """
        Change actor ID. Should be called when switching to another user ID
        @param actor_id:
        @return:
        """
        self.id = actor_id
        self.request.session['actor_id'] = actor_id
        log.debug("Switched actor identity to %s" % actor_id)

    def logout(self):
        """
        Log out
        @return:
        """
        log.debug("Logging out %s" % self.real_id)

        self.real_id = None
        self.id = None
        self.request.session.expire()

        self.request.session.reset()

    def logout_all(self):
        """
        Log out all sessions for this (real) user
        @return:
        """
        log.debug("Logging out all %s" % self.real_id)

        self.real_id = None
        self.id = None
        self.request.session.expire_match({'real_id': self.id})
        self.request.session.reset()

    def changed_credentials(self):
        """
        Changed (actor) credentials. Should be called when the users authentication tokens are changed, ie when they
        change their password or oauth token.
        
        @return:
        """
        log.debug("Changing credentials %s (real) acting as %s" % (self.real_id, self.id))

        assert self.id, 'You cannot change credentials without a valid identity'
        self.request.session.expire_match({'actor_id': self.id})
        if self.id == self.real_id:
            self.request.session.rotate()


def on_request(event):
    """
    Decorate request with identity (must be called after Session)
    @param event:
    @return:
    """
    event.request.identity = Identity(event.request)