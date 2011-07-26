from pika.adapters import SelectConnection
from pika.adapters.blocking_connection import BlockingConnection
from pika.connection import ConnectionParameters
from pika import BasicProperties
from json import dumps
import time

connection = BlockingConnection(ConnectionParameters('127.0.0.1'))
channel=connection.channel()
channel.queue_declare(queue="test")

def consume(channel, method, properties, body):
    print "got",body

channel.basic_consume(consume, queue='test', no_ack=True)

channel.start_consuming()

connection.close()
