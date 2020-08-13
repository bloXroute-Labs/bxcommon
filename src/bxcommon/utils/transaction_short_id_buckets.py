from collections import defaultdict
from dataclasses import dataclass
from typing import Dict

from bxcommon import constants


@dataclass
class BucketInfo:
    count: int
    max: int


class TransactionShortIdBuckets:
    buckets: Dict[int, BucketInfo]

    def __init__(self):
        self.buckets = defaultdict(lambda: BucketInfo(0, 0))

    def incr_short_id(self, short_id: int) -> None:
        bucket = short_id - (short_id % constants.TX_SID_INTERVAL)
        existing_bucket_info = self.buckets[bucket]
        if short_id > existing_bucket_info.max:
            existing_bucket_info.max = short_id
        existing_bucket_info.count += 1

    def __repr__(self):
        return repr(self.buckets)
