import json
class ProcessSource5:

    def __init__(self, logger) -> None:
        self.logger = logger
        pass

    def process(self, payload):
        self.logger.info("Process EP5")
        
        self.logger.info(payload)
        payload = json.loads(payload)
        self.logger.info(payload['node_id'])

        # print(payload['node_id'])