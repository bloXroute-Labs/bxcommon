import gc
from collections import defaultdict
from typing import Dict
from typing import Type, Any, TYPE_CHECKING

from bxcommon import constants
from bxcommon.utils.stats.statistics_service import StatsIntervalData, StatisticsService
from bxutils import logging
from bxutils.logging import LogRecordType

if TYPE_CHECKING:
    # noinspection PyUnresolvedReferences
    # pylint: disable=ungrouped-imports,cyclic-import
    from bxcommon.connections.abstract_node import AbstractNode


class NodeTransactionStatInterval(StatsIntervalData):
    total_uncollectable: int
    generation_zero_size: int
    generation_one_size: int
    generation_two_size: int
    time_spent_in_gc: int
    collection_counts: Dict[int, int]

    def __init__(self, *args, **kwargs):
        super(NodeTransactionStatInterval, self).__init__(*args, **kwargs)
        self.total_uncollectable = 0
        self.generation_zero_size = 0
        self.generation_one_size = 0
        self.generation_two_size = 0
        self.collection_counts = defaultdict(int)
        self.generation_zero_collections = 0
        self.generation_one_collections = 0
        self.generation_two_collections = 0
        self.time_spent_in_gc = 0


class _NodeStatisticsService(StatisticsService[NodeTransactionStatInterval, "AbstractNode"]):
    def __init__(self, interval: int = constants.NODE_STATS_INTERVAL_S):
        super().__init__(
            "NodeStatus",
            interval,
            reset=True,
            stat_logger=logging.get_logger(LogRecordType.NodeStatus, __name__),
        )

    def get_interval_data_class(self) -> Type[NodeTransactionStatInterval]:
        return NodeTransactionStatInterval

    def get_info(self) -> Dict[str, Any]:
        assert self.interval_data is not None
        gen0, gen1, gen2 = gc.get_count()
        return {
            "garbage_collection": {
                "uncollectable": len(gc.garbage),
                "collection_counts": {
                    # pyre-fixme[16]: Optional type has no attribute
                    #  `collection_counts`.
                    f"gen{k}": v for k, v in self.interval_data.collection_counts.items()
                },
                "sizes": {"gen0": gen0, "gen1": gen1, "gen2": gen2,},
                # pyre-fixme[16]: Optional type has no attribute `time_spent_in_gc`.
                "total_elapsed_time": self.interval_data.time_spent_in_gc,
            }
        }

    def log_gc_duration(self, generation: int, duration_s: int) -> None:
        assert self.interval_data is not None
        # pyre-fixme[16]: Optional type has no attribute `time_spent_in_gc`.
        self.interval_data.time_spent_in_gc += duration_s
        # pyre-fixme[16]: Optional type has no attribute `collection_counts`.
        self.interval_data.collection_counts[generation] += 1


node_stats_service = _NodeStatisticsService()
