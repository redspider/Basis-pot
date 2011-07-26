from pyramid.view import view_config
from netl.lib.session import InvalidCSRFToken

@view_config(route_name='session_test', renderer='json')
def session_test(request):
    request.session['number'] = request.session.get('number',0) + 1

    return {'id': request.session['number']}

@view_config(route_name='session_rotate', renderer='json')
def session_rotate(request):
    request.session.rotate()
    return {'status': 'done'}

@view_config(route_name='session_expire', renderer='json')
def session_expire(request):
    request.session.expire()
    return {'status': 'done'}

@view_config(route_name='csrf_get', renderer='json')
def csrf_get(request):
    token = request.session.create_csrf_token()
    return {'token': token}

@view_config(route_name='csrf_check', renderer='json')
def csrf_check(request):
    token = request.params.get('token')
    try:
        request.session.consume_csrf_token(token)
    except InvalidCSRFToken:
        return {'status': 'failed'}
    return {'status': 'ok'}

