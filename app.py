import os
import logging
from dotenv import load_dotenv
from threading import Thread, Lock
from utils.argument_tools import ParserHelper
from utils.log_tools import LoggerHelper
from protocol.mqtt_wrapper import MQTTWrapper

from __about__ import __version__ as app_version, __pkg_name__

# Load environment variables from the .env file in the parent directory
load_dotenv('app_service.env')

class ApplicationService(Thread):
    
    def __init__(self, settings, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.logger.info("Version is: %s", app_version)

        print('before super')
        super(ApplicationService, self).__init__()

        print('after super')
        last_will_topic = "gw-event/last-will-topic"
        last_will_message = "last-will-topic"
        
        self.mqtt_wrapper = MQTTWrapper(
            settings,
            self.logger,
            self._on_mqtt_wrapper_termination_cb,
            self.on_connect,
            last_will_topic,
            last_will_message,
        )
        self.mqtt_wrapper.start()

        self.test = "test"

    def on_connect(self):
        topic = "gw-event/received_data/#"
        self.mqtt_wrapper.subscribe(
            topic, self._on_received_data
        )

    def _on_received_data(self, client, userdata, message):
        print(message.payload)

    def _on_mqtt_wrapper_termination_cb(self):
        
        self.logger.error("MQTT wrapper ends. Terminate the program")
        

def main():
    """
        Main service for Application module

    """
    parse = ParserHelper(
        description="Sump Pump Application service arguments",
        version=app_version,
    )

    parse.add_file_settings()
    parse.add_mqtt()
    settings = parse.settings()

    # Set default debug level
    debug_level = "info"
    try:
        debug_level = os.environ["DEBUG_LEVEL"]
        print(
            "Deprecated environment variable DEBUG_LEVEL "
            "(it will be dropped from version 2.x onwards)"
            " please use WM_DEBUG_LEVEL instead."
        )
    except KeyError:
        pass

    try:
        debug_level = os.environ["WM_DEBUG_LEVEL"]
    except KeyError:
        pass

    log = LoggerHelper(module_name=__pkg_name__, level=debug_level)
    logger = log.setup()

    ApplicationService(settings=settings, logger=logger).run()


if __name__ == "__main__":
    main()