from decorator import decorator

user_lookup = None

class NoUserException(Exception):
    pass

class InsufficientPermissionsException(Exception):
    pass

class Identities(object):
    real = None
    actor = None
    def __init__(self, real, actor):
        self.real = real
        self.actor = actor

def _augment_request(request):
    if not request.identity.is_set():
        raise NoUserException()

    request.auth = user_lookup(request.identity.real_id, request.identity.id)

    if not request.auth:
        raise NoUserException()

def require_user():
    """
    Decorator that demands a user from the request

    @return:
    """
    def require_user(f, request):
        _augment_request(request)

        return f(request)
    return decorator(require_user)

def require_admin():
    """
    Decorator that demands an admin from the request
    
    :return:
    """
    def require_admin(f, request):
        _augment_request(request)

        if request.auth.user['role'] != 'admin':
            raise InsufficientPermissions()

        return f(request)
    return decorator(require_admin)


def init(lookup):
    global user_lookup

    user_lookup=lookup