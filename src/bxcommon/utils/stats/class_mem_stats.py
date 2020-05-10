from collections import defaultdict


class ClassMemStats:
    def __init__(self):
        self.timestamp = 0
        self.networks = defaultdict(ClassMemNetworks)


class ClassMemNetworks:
    def __init__(self):
        self.analyzed_objects = defaultdict(ClassMemObjects)


class ClassMemObjects:
    def __init__(self):
        self.object_item_count = 1
        self.object_size = 0
        self.object_flat_size = 0
        self.object_type = None
        self.size_type = None
