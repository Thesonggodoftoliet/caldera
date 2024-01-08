# rpc_client.py
import pika
import uuid

MQ_HOST = "192.168.0.108"
MQ_PORT = 5672
MQ_USER = "cipc"
MQ_PASSWORD = "cipc9508"


class RpcClient(object):

    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=MQ_HOST, port=MQ_PORT,
                                      credentials=pika.PlainCredentials(username=MQ_USER, password=MQ_PASSWORD))
        )
        self.channel = self.connection.channel()
        # result = self.channel.queue_declare(queue='tut.rpc.requests')
        self.callback_queue = 'rpc.request'

        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True)

        self.response = None
        self.corr_id = None

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def call(self, msg):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='rpc',
            routing_key='rpc',
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=msg)
        self.connection.process_data_events(time_limit=None)
        return self.response.decode("utf-8")

