"""
Authentication via Facebook OAuth 2.0

sign_in should be opened in a new (facebook-sized) window. At the completion of the sign in and authentication,
the callback page will trigger an event on the parent then close.


"""

def sign_in(request):
    """
    Simply redirects to fb authorize url

    """
    pass

def authenticate(request):
    """
    Accept provided code, generate access url, request access token from access url
    use access token to obtain user data if needed
    """
    pass