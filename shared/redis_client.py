import redis
from threading import Thread, Event
import threading
import logging

class RedisClient(Thread):
    def __init__(self, logger=None, host='redis', port=6379):
        Thread.__init__(self)
        # logger
        self.logger = logger or logging.getLogger(__name__)

        # client
        self.client = redis.Redis(host=host, port=port, decode_responses=True)

        # pubsub
        self.subscriber = self.client.pubsub()
        # self.subscriber.psubscribe
        # thread for listening messages
        # self.thread = Thread(target=self._handle_messages)
        # self.callback = None
        # self.channel = None
        # self.stop_event = threading.Event()
        
        self.logger.info("Initializing Redis Client")

    # def run(self):
    #     self.start()

    # def start(self):
    #     self.thread.start()
    #     self.logger.info("Start Threading")

    # def stop(self):
    #     self.stop_event.set()
    #     self.thread.join()

    # def _handle_messages(self):
    #     for message in self.subscriber.listen():
    #         self.logger.info(message)
    #         # self.callback(decoded_message)
    #         if message['type'] == 'message':
    #             decoded_message = message['data'].decode('utf-8')
    #             self.logger.info(decoded_message)
    #             if self.callback:
    #                 self.callback(decoded_message)

    def subscribe(self, channel, callback):
        
        self.subscriber.subscribe(**{channel: callback})
        self.subscriber.run_in_thread(sleep_time=0.1)
        # if not self.channel and not self.callback:
        #     self.channel = channel
        #     self.callback = callback
        #     self.subscriber.subscribe(channel=channel,)
        # else:
        #     raise ValueError("RedisClient can only subscribe to one channel and one callback.")

    def redis_message(self, message):
        if message and message.get('type') == 'message':
            return message.get('data')
        return False
    
    def publish_message(self, channel, message):
        self.client.publish(channel, message)