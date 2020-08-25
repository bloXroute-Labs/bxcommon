import gc
import dataclasses
import functools

from dataclasses import dataclass
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


@dataclass
class NodeTransactionStatInterval(StatsIntervalData):
    total_uncollectable: int = 0
    generation_zero_size: int = 0
    generation_one_size: int = 0
    generation_two_size: int = 0
    time_spent_in_gc: float = 0
    collection_counts: Dict[int, int] = dataclasses.field(default_factory=functools.partial(defaultdict, int))
    generation_zero_collections: int = 0
    generation_one_collections: int = 0
    generation_two_collections: int = 0


class _NodeStatisticsService(StatisticsService[NodeTransactionStatInterval, "AbstractNode"]):
    def __init__(self, interval: int = constants.NODE_STATS_INTERVAL_S) -> None:
        super().__init__(
            "NodeStatus",
            interval,
            reset=True,
            stat_logger=logging.get_logger(LogRecordType.NodeStatus, __name__),
        )

    def get_interval_data_class(self) -> Type[NodeTransactionStatInterval]:
        return NodeTransactionStatInterval

    def get_info(self) -> Dict[str, Any]:
        interval_data = self.interval_data
        assert interval_data is not None
        gen0, gen1, gen2 = gc.get_count()
        return {
            "garbage_collection": {
                "uncollectable": len(gc.garbage),
                "collection_counts": {
                    f"gen{k}": v for k, v in interval_data.collection_counts.items()
                },
                "sizes": {"gen0": gen0, "gen1": gen1, "gen2": gen2,},
                "total_elapsed_time": interval_data.time_spent_in_gc,
            }
        }

    def log_gc_duration(self, generation: int, duration_s: float) -> None:
        self.interval_data.time_spent_in_gc += duration_s
        self.interval_data.collection_counts[generation] += 1


node_stats_service = _NodeStatisticsService()
