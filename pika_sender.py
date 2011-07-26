from pika.adapters import SelectConnection
from pika.adapters.blocking_connection import BlockingConnection
from pika.connection import ConnectionParameters
from pika import BasicProperties
from json import dumps
import time

connection = BlockingConnection(ConnectionParameters('127.0.0.1'))
channel=connection.channel()
channel.queue_declare(queue="test")

start = time.time()

for i in xrange(0,100000):
    channel.basic_publish(exchange='', routing_key='test', body=dumps({'quack': 'duck'}))

print "100000 messages in %d s" % (time.time()-start)

connection.close()
