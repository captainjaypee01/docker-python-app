import paho.mqtt.client as mqtt
import queue
import os
import socket
import ssl
from select import select
from time import sleep
from threading import Thread, Lock
from paho.mqtt.client import connack_string
from protocol.mqtt_helper import SelectableQueue, PublishMonitor

class MQTTWrapper(Thread):
    
    # Keep alive time with broker
    KEEP_ALIVE_S = 20

    def __init__(self, 
                settings,
                logger,
                on_termination_cb=None,
                on_connect_cb=None,
                last_will_topic=None,
                last_will_data=None,
    ):
        Thread.__init__(self)
        self.logger = logger
        self.on_termination_cb = on_termination_cb
        self.on_connect_cb = on_connect_cb
        self.client = mqtt.Client()

        
        if not settings.mqtt_force_unsecure:
            try:
                self.client.tls_set(
                    ca_certs=settings.mqtt_ca_certs,
                    certfile=settings.mqtt_certfile,
                    keyfile=settings.mqtt_keyfile,
                    cert_reqs=ssl.VerifyMode[settings.mqtt_cert_reqs],
                    tls_version=ssl._SSLMethod[settings.mqtt_tls_version],
                    ciphers=settings.mqtt_ciphers,
                )
            except Exception as e:
                self.logger.error("Cannot use secure authentication %s", e)
                exit(-1)

        self.client.on_connect = self._on_connect
        self.client.on_publish = self._on_publish
        self.client.on_disconnect = self._on_disconnect
        
        self.client.connect(settings.mqtt_hostname, settings.mqtt_port)
        
        if last_will_topic is not None and last_will_data is not None:
            last_will_topic = "gw-event/last-will"
            self._set_last_will(last_will_topic, last_will_data)

        try:
            self.client.connect(
                settings.mqtt_hostname,
                settings.mqtt_port,
                keepalive=MQTTWrapper.KEEP_ALIVE_S,
            )
        except (socket.gaierror, ValueError) as e:
            self.logger.error(
                "Error on MQTT address %s:%d => %s"
                % (settings.mqtt_hostname, settings.mqtt_port, str(e))
            )
            exit(-1)
        except ConnectionRefusedError:
            self.logger.error("Connection Refused by MQTT broker")
            exit(-1)

        self._publish_queue = SelectableQueue()
        # Thread is not started yes
        self.running = False
        self.connected = False
        self.first_connection_done = False
        # self.queue = queue.Queue()
        # self.thread = Thread(target=self.worker)
        # self.thread.start()
    
    def _on_connect(self, client, userdata, flags, rc):
        # pylint: disable=unused-argument
        if rc != 0:
            self.logger.error("MQTT cannot connect: %s (%s)", connack_string(rc), rc)
            self.running = False
            return

        self.first_connection_done = True
        self.connected = True
        if self.on_connect_cb is not None:
            self.on_connect_cb()

    def _on_disconnect(self, userdata, rc):
        if rc != 0:
            os.system("sudo systemctl stop wirepasSink1.service")
            self.logger.info("Stop Sink Service")
            self.logger.error(
                "MQTT unexpected disconnection (network or broker originated):"
                "%s (%s)",
                connack_string(rc),
                rc,
            )
            self.connected = False
            
    def _do_select(self, sock):
        # Select with a timeout of 1 sec to call loop misc from time to time
        r, w, _ = select(
            [sock, self._publish_queue],
            [sock] if self.client.want_write() else [],
            [],
            1,
        )

        if sock in r:
            self.client.loop_read()

        if sock in w:
            self.client.loop_write()

        self.client.loop_misc()

        # Check if we have something to publish
        if self._publish_queue in r:
            try:
                # Publish everything. Loop is not necessary as
                # next select will exit immediately if queue not empty
                while True:
                    topic, payload, qos, retain = self._publish_queue.get()

                    self._publish_from_wrapper_thread(
                        topic, payload, qos=qos, retain=retain
                    )

                    # FIX: read internal sockpairR as it is written but
                    # never read as we don't use the internal paho loop
                    # but we have spurious timeout / broken pipe from
                    # this socket pair
                    # pylint: disable=protected-access
                    try:
                        self.client._sockpairR.recv(1)
                    except Exception:
                        # This socket is not used at all, so if something is wrong,
                        # not a big issue. Just keep going
                        pass

            except queue.Empty:
                # No more packet to publish
                pass
      
    def _get_socket(self):
        sock = self.client.socket()
        if sock is not None:
            return sock

        if self.connected:
            os.system("sudo systemctl stop wirepasSink1.service")
            self.logger.info("Stop Sink Service")
            self.logger.error("MQTT Inner loop, unexpected disconnection")
        elif not self.first_connection_done:
            # It's better to avoid retrying if the first connection was not successful
            self.logger.error("Impossible to connect - authentication failure ?")
            return None

        # Socket is not opened anymore, try to reconnect for timeout if set
        loop_forever = self.timeout == 0
        delay = 0
        self.logger.info("Starting reconnect loop with timeout %d" % self.timeout)
        # Loop forever or until timeout is over
        while loop_forever or (delay <= self.timeout):
            try:
                self.logger.debug("MQTT reconnect attempt delay=%d" % delay)
                ret = self.client.reconnect()
                if ret == mqtt.MQTT_ERR_SUCCESS:
                    break
            except Exception:
                # Retry to connect in 1 sec up to timeout if set
                sleep(1)
                delay += 1
                self.logger.debug("Retrying to connect in 1 sec")

        if not loop_forever:
            # In case of timeout set, check if it exits because of timeout
            if delay > self.timeout:
                self.logger.error("Unable to reconnect after %s seconds", delay)
                return None

        # Socket must be available once reconnect is successful
        if self.client.socket() is None:
            self.logger.error("Cannot get socket after reconnect")
            return None
        else:
            self.logger.info("Successfully acquired socket after reconnect")

        # Set options to new reopened socket
        if not self._use_websockets:
            self.client.socket().setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 2048)
        return self.client.socket()
    
    def _set_last_will(self, topic, data):
        # Set Last wil message
        self.logger.info("Last will")
        self.client.will_set(topic, data, qos=2, retain=True)

    def run(self):
        self.running = True

        while self.running:

            try:
                # check if we are connected
                # Get client socket to select on it
                # This function manage the reconnect
                sock = self._get_socket()
                if sock is None:
                    # Cannot get the socket, probably an issue
                    # with connection. Exit the thread
                    self.logger.error("Cannot get MQTT socket, exit...")
                    self.running = False
                else:
                    self._do_select(sock)
            except TimeoutError:
                self.logger.error("Timeout in connection, force a reconnect")
                self.client.reconnect()
            except Exception:
                # If an exception is not caught before this point
                # All the transport module must be stopped in order to be fully
                # restarted by the managing agent
                self.logger.exception("Unexpected exception in MQTT wrapper Thread")
                self.running = False

        if self.on_termination_cb is not None:
            # As this thread is daemonized, inform the parent that this
            # thread has exited
            self.on_termination_cb()

    def _on_publish(self, client, userdata, mid):
        self._unpublished_mid_set.remove(mid)
        self._publish_monitor.on_publish_done()
        return
    
    def worker(self):
        while True:
            topic, payload = self.queue.get()
            if topic == "sensors/temperature":
                print('temp')
                # on_temperature(payload, "Celsius")
            elif topic == "sensors/humidity":
                print('humidity')
                # on_humidity(payload)
            self.queue.task_done()
    
    def publish(self, topic, message):
        self.client.publish(topic, message)

    def subscribe(self, topic, cb, qos=2) -> None:
        self.logger.debug("Subscribing to: {}".format(topic))
        self.client.subscribe(topic, qos)
        self.client.message_callback_add(topic, cb)