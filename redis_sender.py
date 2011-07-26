import redis
import time

from json import loads, dumps

r = redis.Redis()

def send_message(r, **kwargs):
    r.publish('test_log', dumps(kwargs))

start = time.time()
for i in range(0,100000):
    send_message(r, foo='quack')
print "100000 messages in %d s" % (time.time()-start)