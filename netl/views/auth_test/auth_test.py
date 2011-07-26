from pyramid.view import view_config
from netl.lib import auth

@view_config(route_name='auth_test', renderer='json')
@auth.require_user()
def user_test(request):
    return {'status': 'accepted', 'username': request.auth.user.name}

@view_config(route_name='auth_login', renderer='json')
def user_login(request):
    request.identity.set(1,1)
    return {'status': 'logged in'}



@view_config(context=auth.NoUserException, renderer='json')
def on_no_user(request):
    return {'status': 'no such user. log in you lazy bastard'}

@view_config(context=auth.InsufficientPermissionsException, renderer='json')
def on_not_admin(request):
    return {'status': 'if only you were an admin'}