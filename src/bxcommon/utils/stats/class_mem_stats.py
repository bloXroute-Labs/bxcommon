from collections import defaultdict
from datetime import datetime


class ClassMemStats:
    def __init__(self) -> None:
        self.timestamp: datetime = datetime.utcnow()
        self.networks = defaultdict(ClassMemNetworks)


class ClassMemNetworks:
    def __init__(self) -> None:
        self.analyzed_objects = defaultdict(ClassMemObjects)


class ClassMemObjects:
    def __init__(self) -> None:
        self.object_item_count = 1
        self.object_size = 0
        self.object_flat_size = 0
        self.object_type = None
        self.size_type = None
