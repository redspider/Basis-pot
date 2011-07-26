import netl.lib.db as db

class RequestAuth(object):
    real = None
    user = None

    def __init__(self, real=None, actor=None):
        self.real = real
        self.user = actor

def get_request_object(real_id, actor_id):
    """
    Retrieve real and actor rows from database

    :param real_id:
    :param actor_id:
    :return: RequestAuth instance or None
    """
    accounts = list(db.query("SELECT * FROM account WHERE id IN (:real_id, :actor_id) AND status='active'", real_id=real_id, actor_id=actor_id).fetchall())

    if not accounts:
        return None

    if len(accounts) < 2:
        if accounts[0]['id'] != real_id:
            return None

        return RequestAuth(accounts[0], accounts[0])

    if accounts[0]['id'] == real_id:
        return RequestAuth(accounts[0], accounts[1])
    else:
        return RequestAuth(accounts[1], accounts[0])


def local_authenticate(username, password):
    """
    Check username and password are valid (does not check the account is active etc), returns account id

    :param username:
    :param password:
    :return:
    """

    # use hash and verify from pcrypt

    pass

def local_sign_up(username, password, email):
    """
    Create a local account and identity

    :param username:
    :param password:
    :param email:
    :return:
    """

    pass

def get_for_session(account):
    """
    Retrieve account details necessary to feed session

    :param account:
    :return:
    """

    pass

def can_login(account):
    """
    Is this account permitted to log in? (might be disabled etc)
    
    :param account:
    :return:
    """

    pass