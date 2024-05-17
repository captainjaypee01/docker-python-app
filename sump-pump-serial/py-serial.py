import serial
import serial.tools.list_ports
import serial.serialutil
import threading
# from pydbus import SystemBus
# from dbus.dbus_client import DBusClient
import time
import logging
from utils.log_tools import LoggerHelper
from shared.redis_client import RedisClient

SERIAL_PORT = "/dev/ttyAMA0"
class SerialPortListener():
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)

        self.serial_port = SERIAL_PORT
        self.serial_port_instance = None
        # self.obj = self.bus.publish("com.example.SerialPortListener", self)
        self.listening_thread = None
        self.stop_event = threading.Event()

        self.redis_client = RedisClient(logger=logger)
        self.redis_client.start()
        self.logger.info("Initializing Serial Port Listener")

    def is_serial_port_available(self):
        try:
            with serial.Serial(self.serial_port) as test_serial:
                return True
        except serial.serialutil.SerialException:
            return False


    def initialize_serial_port(self):
        try:
            self.serial_port_instance = serial.Serial(
                self.serial_port,
                baudrate=115200,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1
            )
            self.logger.info(f"Serial port {self.serial_port} initialized successfully.")
        except serial.serialutil.SerialException:
            self.logger.info(f"Failed to initialize serial port {self.serial_port}.")

    def read_serial_data(self):
        while not self.stop_event.is_set():
            if self.serial_port_instance is None:
                self.logger.info("Serial port not initialized. Waiting for initialization...")
                time.sleep(5)
                continue

            try:
                while not self.stop_event.is_set():
                    data = self.serial_port_instance.readline()
                    if data:
                        self.logger.info(f"Received from serial port: {data}")
                        self.redis_client.publish_message('gw-event/received_data', data)
                        # Send data to redis below here...

            except serial.serialutil.SerialException:
                self.logger.info(f"Serial port {self.serial_port} disconnected. Reinitializing...")
                self.initialize_serial_port()

    def start_listening_thread(self):
        
        
        while not self.is_serial_port_available():
            self.logger.info(f"Serial port {self.serial_port} not available. Retrying in 5 seconds...")
            time.sleep(5)

        self.logger.info(f"Serial port {self.serial_port} is available. Starting listening thread.")
        self.listening_thread = threading.Thread(target=self.read_serial_data)
        self.listening_thread.start()

        # if self.is_serial_port_available():
        #     print(f"Serial port {self.serial_port} is available. Starting listening thread.")
        #     self.listening_thread = threading.Thread(target=self.read_serial_data)
        #     self.listening_thread.start()
        # else:
        #     print(f"Serial port {self.serial_port} not available. Will retry.")
            
    def stop_listening_thread(self):
        if self.listening_thread:
            self.logger.info("Stopping listening thread...")
            self.stop_event.set()
            self.listening_thread.join()
            self.logger.info("Listening thread stopped.")
            self.redis_client.stop()

    def redis_test_send_data(self, message):
        
        # Send test data to redis below here...
        self.logger.info(f"TEST MESSAGE {message}")
        self.redis_client.publish_message('gw-event/received_data', message)
        pass


def main():
    debug_level = "info"
    log = LoggerHelper(module_name="sump_pump_serial", level=debug_level)
    logger = log.setup()

    logger.info("Start Main")
    serialApp = SerialPortListener(logger=logger)
    serialApp.start_listening_thread()

    try:
        logger.info("Start Sending Data To Redis")
        cnt = 1
        while True:
            # Your main application logic can go here
            serialApp.redis_test_send_data(f"HELLO WORLD {cnt}")
            # serialApp.redis_test_send_data("HELLO WORLD 2")
            # serialApp.redis_test_send_data("HELLO WORLD 3")
            # serialApp.redis_test_send_data("HELLO WORLD 4")
            cnt = cnt + 1
            if(cnt == 100):
                cnt = 1
            time.sleep(5)
    except KeyboardInterrupt:
        logger.info("Stopping the application...")
        # serialApp.stop_listening_thread()

if __name__ == "__main__":
    main()