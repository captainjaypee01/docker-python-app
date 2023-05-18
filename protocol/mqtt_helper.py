
import os
import queue
import socket
import ssl
from threading import Thread, Lock
from time import sleep
from datetime import datetime

class SelectableQueue(queue.Queue):
    """
    Wrapper arround a Queue to make it selectable with an associated
    socket
    """

    def __init__(self):
        super().__init__()
        self._putsocket, self._getsocket = socket.socketpair()
        self._lock = Lock()
        self._size = 0

    def fileno(self):
        """
        Implement fileno to be selectable
        :return: the reception socket fileno
        """
        return self._getsocket.fileno()

    def put(self, item, block=True, timeout=None):
        with self._lock:
            if self._size == 0:
                # Send 1 byte on socket to signal select
                self._putsocket.send(b"x")
            self._size = self._size + 1

            # Insert item in queue
            super().put(item, block, timeout)

    def get(self, block=False, timeout=None):
        with self._lock:
            # Get item first so get can be called and
            # raise empty exception
            item = super().get(block, timeout)

            self._size = self._size - 1
            if self._size == 0:
                # Consume 1 byte from socket
                self._getsocket.recv(1)
            return item


class PublishMonitor:
    """
        Object dedicated to MQTT publish monitoring, in a simple
        and "Thread-safe" way.
    """

    def __init__(self):
        self._lock = Lock()
        self._size = 0
        self._last_publish_event_timestamp = 0  # valid if size != 0

    def get_publish_queue_size(self):
        with self._lock:
            return self._size

    def get_publish_waiting_time_s(self):
        with self._lock:
            if self._size == 0:
                return 0
            else:
                delta = datetime.now() - self._last_publish_event_timestamp
                return delta.total_seconds()

    def on_publish_request(self):
        with self._lock:
            if self._size == 0:
                self._last_publish_event_timestamp = datetime.now()
            self._size = self._size + 1

    def on_publish_done(self):
        with self._lock:
            self._size = self._size - 1
            self._last_publish_event_timestamp = datetime.now()