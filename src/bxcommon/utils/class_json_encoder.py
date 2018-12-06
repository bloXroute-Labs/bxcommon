import json
from datetime import datetime


class ClassJsonEncoder(json.JSONEncoder):

    def default(self, o):
        if hasattr(o, '__dict__'):
            return o.__dict__
        if isinstance(o, datetime):
            return o.__str__()
        return o
