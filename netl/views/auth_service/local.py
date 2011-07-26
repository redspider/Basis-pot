"""
Local authentication service

Works differently from the others since it assumes the JS app knows the username and password, and thus can
request authenticate directly.

"""
from netl.lib import validate

import netl.model as m

def authenticate(request):
    """
    Accept email address, password in POST, set up session if valid otherwise hand back error in json
    """

    username = validate.username(request.POST['username'])
    password = validate.password(request.POST['password'])

    if not m.user.local_authenticate(username, password):
        # Return an error, u/p invalid or whatever
        pass

    # Retrieve user
    user = m.user.get_for_session(username)

    # Check login status
    if not m.user.can_login(user.id):
        # Return an error, matching status issue
        pass

    # Set up identity session
    # Return user info to json

def sign_up(request):
    """
    Create user given email address, password
    """
    username = validate.username(request.POST['username'])
    password = validate.password(request.POST['password'])
    email = validate.email(request.POST['email'])

    # Create user
    user = m.user.local_sign_up(username, password, email)

    # Failed? probably a username in use
    if not user:
        # return error
        pass

    # set up identity session
    # return user info to json


