import json


class ThroughputPayloadEncoder(json.JSONEncoder):

    def default(self, o):
        return o.__dict__
