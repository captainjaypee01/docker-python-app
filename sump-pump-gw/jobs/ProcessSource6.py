import json
class ProcessSource6:

    def __init__(self, logger) -> None:
        self.logger = logger
        pass

    def process(self, payload):
        self.logger.info("Process EP6")
        
        self.logger.info(payload)
        payload = json.loads(payload)
        self.logger.info(payload['node_id'])

        # print(payload['node_id'])