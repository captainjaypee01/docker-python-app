import json
class ProcessSource152:

    def __init__(self, logger) -> None:
        self.logger = logger
        pass

    def process(self, payload):
        self.logger.info("Process EP152")
        
        self.logger.info(payload)
        payload = json.loads(payload)
        self.logger.info(payload['node_id'])

        # print(payload['node_id'])