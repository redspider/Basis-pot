import redis

from json import loads, dumps

def receive_message(**kwargs):
    pass

r = redis.Redis().pubsub()
r.subscribe(['test_log'])

for message in r.listen():
    pass
    
