import json


class ClassJsonEncoder(json.JSONEncoder):

    def default(self, o):
        if hasattr(o, '__dict__'):
            return o.__dict__

        return o
