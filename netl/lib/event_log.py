"""

Event log

Logs events into mongodb for analysis. Also offers event handlers to log pretty much everything from a request/response
including timing information.

Configuration

event_log.mongodb_url     MongoDB url
event_log.mongodb_db      MongoDB database

Usage

import event_log

event_log.warn('auth',user=request.auth,action='Attempt to access admin controls')


"""
from datetime import datetime
import logging
import pymongo

config = {}
mongodb = None

logging.basicConfig()
log = logging.getLogger(__file__)
log.setLevel(logging.DEBUG)

def send(source, priority, **kwargs):
    kwargs['dated'] = datetime.now()
    kwargs['source'] = source
    kwargs['priority'] = priority
    mongodb[config['mongodb_db']].log.insert(kwargs)

def debug(source, **kwargs):
    send(source, 'debug', **kwargs)

def info(source, **kwargs):
    send(source, 'info', **kwargs)

def warn(source, **kwargs):
    send(source, 'warn', **kwargs)

def error(source, **kwargs):
    send(source, 'error', **kwargs)



def on_request(event):
    """
    Log start of request

    @param event:
    @return:
    """
    event.request._tracking = {
        'start': datetime.now()
    }

def on_response(event):
    """
    Log request/response cycle
    
    @param event:
    @return:
    """
    entry = dict()
    entry['start'] = event.request._tracking['start']
    entry['end'] = datetime.now()
    entry['session'] = event.request.session.id

    if hasattr(event.request,'auth') and event.request.auth:
        entry['auth'] = event.request.auth

    if event.request.GET:
        entry['GET'] = dict(event.request.GET)

    if event.request.POST:
        entry['POST'] = dict(event.request.POST)

    entry['method'] = event.request.method
    entry['req_headers'] = dict(event.request.headers)
    entry['url'] = event.request.path_qs
    entry['status'] = event.response.status
    entry['res_headers'] = dict(event.response.headers)

    info('request',**entry)



def init(settings):
    """
    Initialise event log subsystem

    @param settings:dict Event log configuration settings (see module docs)
    @return:
    """
    global mongodb

    mongodb = pymongo.Connection(settings.get('event_log.mongodb_url'))
    config['mongodb_db'] = settings.get('event_log.mongodb_db')
