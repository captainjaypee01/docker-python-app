import os
import logging
import sys
import json
from queue import Queue
from dotenv import load_dotenv
from threading import Thread, Lock
from utils.argument_tools import ParserHelper
from utils.log_tools import LoggerHelper
from protocol.mqtt_wrapper import MQTTWrapper
from datetime import datetime

from __about__ import __version__ as app_version, __pkg_name__

#jobs
from jobs.ProcessSource1 import ProcessSource1
from jobs.ProcessSource5 import ProcessSource5
from jobs.ProcessSource6 import ProcessSource6
from jobs.ProcessSource9 import ProcessSource9
from jobs.ProcessSource146 import ProcessSource146
from jobs.ProcessSource152 import ProcessSource152
from jobs.ProcessWirepasSource import ProcessWirepasSource
from jobs.ProcessSource5 import ProcessSource5

# Load environment variables from the .env file in the parent directory
load_dotenv('app_service.env')

# Import Protocol Buffers message classes
sys.path.insert(0, "proto-py")
import generic_message_pb2 as generic_message
import wp_global_pb2 as wp_global
import data_message_pb2 as data_message

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
        self.messages_process_thread = Thread(target=self.message_worker)
        self.message_queue = Queue()
        self.messages_process_thread.start()

    def on_connect(self):
        topic = "gw-event/received_data/#"
        self.mqtt_wrapper.subscribe(
            topic, self._on_received_data
        )

    def _on_received_data(self, client, userdata, message):
        now = datetime.utcnow()
        proto_msg = generic_message.GenericMessage()
        proto_msg.ParseFromString(message.payload)
        recv_packet = proto_msg.wirepas.packet_received_event
        
        nodeid = str(hex(recv_packet.source_address)).replace("0x","")
        networkid = str(hex(recv_packet.network_address)).replace("0x","")
        data = recv_packet.payload.hex()
        # print(recv_packet)
        dataStr = '{{"GatewayID":"{gatewayid}","NetworkID":"{network}","NodeID":"{node}","System":{system},"EP":{ep},"Data":"{datapack}","Timestamp":{time},"Travel":{travel},"Hop":{hop}}}'.format(
                   gatewayid=recv_packet.header.gw_id,
                   network=networkid,
                   node=nodeid,
                   system=recv_packet.source_endpoint,
                   ep=recv_packet.destination_endpoint,
                   datapack=data,
                   time=recv_packet.rx_time_ms_epoch,
                   travel=recv_packet.travel_time_ms,
                   hop=recv_packet.hop_count
                 )

        # Define the job payload
        job_data = {
            'gateway_id': recv_packet.header.gw_id,
            'network_id': networkid,
            'node_id': nodeid,
            'source_endpoint': recv_packet.source_endpoint,
            'destination_endpoint': recv_packet.destination_endpoint,
            'data': data,
            'time': recv_packet.rx_time_ms_epoch,
            'travel': recv_packet.travel_time_ms,
            'hop': recv_packet.hop_count,
        }

        self.message_queue.put(job_data)
        #self.process_mqtt(job_data)

        #self.logger.info(dataStr)

    def _on_mqtt_wrapper_termination_cb(self):
        
        self.logger.error("MQTT wrapper ends. Terminate the program")

    def message_worker(self):
        while True:
            message = self.message_queue.get()
            self.process_mqtt(message)
            self.logger.info("job processing", message)
        
    def process_mqtt(self, payload):
        
        jsonPayload = json.dumps(payload)

        if payload['source_endpoint'] == 1 and payload['destination_endpoint'] == 100:
            job = ProcessSource1()
            job.process(jsonPayload)

        if payload['source_endpoint'] == 6 and payload['destination_endpoint'] == 100:
            job = ProcessSource6()
            job.process(jsonPayload)

        if payload['source_endpoint'] == 5:
            job = ProcessSource5()
            job.process(jsonPayload)
            
        if payload['source_endpoint'] == 9 and payload['destination_endpoint'] == 9:
            job = ProcessSource9()
            job.process(jsonPayload)
            
        if payload['source_endpoint'] == 146 and payload['destination_endpoint'] == 155:
            job = ProcessSource146()
            job.process(jsonPayload)
            
        if payload['source_endpoint'] == 152 and payload['destination_endpoint'] == 155:
            job = ProcessSource152()
            job.process(jsonPayload)
            
        if payload['source_endpoint'] == 240 or payload['source_endpoint'] == 247:
            job = ProcessWirepasSource()
            job.process(jsonPayload)
        

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