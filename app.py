"""
Things to work on:

1. Sessions *
2. Authentication *
3. Authorisation *
4. Configuration
5. Views and templates in same space?
6. SQL schema updates and command-line actions
7. Re-integrate mongodb
8. Tests
9. Docs - Sphinx?
10. session flash?
11. Validators
12. Page request ID?
13. Feedback module
14. Javascript error logging to server
15. Facebook/Twitter/Google support
16. Notification (new mail to send, new event logs, possibly comet chatter) - rabbitmq with Node.js for the Sockets.IO
    handler (rabbitmq selected due to acknowledgements and balancing, both of which are near-time useful)

Possible alternate queue option is pusher.com. We could simply operate a client to it and have that client join each channel
in order to do archiving and client disconnect notices. We could use it as a notification backend as well. Dunno, maybe dodgy.


Browser/User communications

User has Browser(s) which have Tab(s)

Users are represented by their user ID
Browsers are represented by the session ID
Tabs are a problem, the session ID is replicated across them but the websocket channel to Node is not. This leaves us with
the option of either sending everything to each tab, or giving the tabs a separate ID, with the caveat that Pyramid cannot
know which tab it's talking to, only Node can (because it's holding the websocket)







Think about how to name package, manage package entry, commandline tools (schema update etc),
maybe paster maybe not. Possibly extra packages possibly not

Maybe turn session into a session factory, maybe not. Right now not, because:
    We're not compatible with ISession
    request-factory is still an option but you can't stack it, so we'd have to put identity, session etc together

"""

import os
import logging
import pymongo
from netl.lib import event_log
import netl.lib.db as db
import netl.lib.session as session
import netl.lib.auth as auth
import netl.model as model

from pyramid.config import Configurator

from paste.httpserver import serve

logging.basicConfig()
log = logging.getLogger(__file__)
log.setLevel(logging.DEBUG)
here = os.path.dirname(os.path.abspath(__file__))


if __name__ == '__main__':
    # configuration settings
    settings = dict()
    settings['reload_all'] = True
    # settings['debug_all'] = True
    settings['debug_authorization'] = False
    settings['debug_notfound'] = True

    settings['mako.directories'] = 'netl:/templates'

    settings['mongo_connection'] = pymongo.Connection('mongodb://localhost/')
    settings['mongo_db_name'] = 'news33'

    settings['session.name'] = 'session'
    settings['session.domain'] = None
    settings['session.path'] = '/'
    settings['session.timeout'] = 10*60
    settings['session.secure_only'] = False
    settings['session.mongodb_url'] = 'mongodb://localhost/'
    settings['session.mongodb_db'] = 'session'

    settings['event_log.mongodb_url'] = 'mongodb://localhost/'
    settings['event_log.mongodb_db'] = 'session'


    settings['sqlalchemy.url'] = 'postgres://richard:test@localhost/netl'

    event_log.init(settings)
    db.init(settings)
    session.init(settings)
    auth.init(model.user.get_request_object)


    config = Configurator(settings=settings)

    config.add_subscriber('netl.lib.event_log.on_request', 'pyramid.events.NewRequest')
    config.add_subscriber('netl.lib.event_log.on_response', 'pyramid.events.NewResponse')

    config.add_subscriber('netl.lib.session.on_request', 'pyramid.events.NewRequest')
    config.add_subscriber('netl.lib.session.on_response', 'pyramid.events.NewResponse')

    config.add_subscriber('netl.lib.identity.on_request', 'pyramid.events.NewRequest')

    config.include('pyramid_tm')

    # Note: routing must be here in one spot for ordering purposes.

    # configuration setup
    config.add_route('session_test','/session_test')
    config.add_route('session_rotate','/session_rotate')
    config.add_route('session_expire','/session_expire')
    config.add_route('csrf_get','/csrf_get')
    config.add_route('csrf_check','/csrf_check')

    config.add_route('auth_test','/auth_test')
    config.add_route('auth_login','/auth_login')


    config.add_route('identity_get','/identity_get')
    config.add_route('identity_login','/identity_login')
    config.add_route('identity_logout','/identity_logout')

    config.add_route('index','/')
    config.add_route('item.add','/news/add')
    config.add_route('item.get','/news/{item}')

    config.add_route('favicon','/favicon.ico')

    config.add_static_view('image', 'netl:/image')
    config.add_static_view('css', 'netl:/css')
    config.add_static_view('js', 'netl:/js')

    config.scan(package='netl.views')

    # serve app
    app = config.make_wsgi_app()
    serve(app, host='127.0.0.1')
    