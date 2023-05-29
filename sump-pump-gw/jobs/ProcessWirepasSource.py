import json
class ProcessWirepasSource:

    def __init__(self, logger) -> None:
        self.logger = logger
        pass

    def process(self, payload):
        self.logger.info("Process WirepasSource")
        
        payload = json.loads(payload)
        self.logger.info(payload)
        self.logger.info(payload['node_id'])

        # print(payload['node_id'])