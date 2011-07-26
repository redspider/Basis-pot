from pyramid.view import view_config

@view_config(route_name='identity_get', renderer='json')
def identity_get(request):
    return {'real': request.identity.real_id, 'actor': request.identity.id}

@view_config(route_name='identity_login', renderer='json')
def identity_login(request):
    request.identity.set('richard','joe')
    return {'status': 'done'}

@view_config(route_name='identity_logout', renderer='json')
def identity_logout(request):
    request.identity.logout()
    return {'status': 'done'}