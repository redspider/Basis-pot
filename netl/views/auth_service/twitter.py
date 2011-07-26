"""
Authentication via twitter service

sign_in should be opened in a new (twitter-sized) window. At the completion of the sign in and authentication,
the callback page will trigger an event on the parent then close.

"""

def sign_in(request):
    """
    Obtain request token, redirect to auth token page
    """
    pass

def authenticate(request):
    """
    Redirect back from Twitter arrives here, verify token then render callback page
    """
    pass