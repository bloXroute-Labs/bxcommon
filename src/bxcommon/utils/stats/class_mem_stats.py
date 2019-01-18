from collections import defaultdict


class ClassMemStats(object):
    def __init__(self):
        self.timestamp = 0
        self.networks = defaultdict(ClassMemNetworks)


class ClassMemNetworks(object):
    def __init__(self):
        self.analyzed_objects = defaultdict(ClassMemObjects)


class ClassMemObjects(object):
    def __init__(self):
        self.object_item_count = 0
        self.object_size = 0
        self.object_flat_size = 0
