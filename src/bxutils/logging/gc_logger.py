import gc
import time
from datetime import datetime
from typing import Dict, Any, Optional

from bxcommon import constants
from bxcommon.utils.stats.node_statistics_service import node_stats_service
from bxutils import logging
from bxutils.logging import LogRecordType

logger = logging.get_logger(LogRecordType.GarbageCollection)

_gc_start: Optional[float] = None


def gc_callback(phase: str, info: Dict[str, Any]):
    # pylint: disable=global-statement
    global _gc_start

    if phase == "start":
        assert _gc_start is None
        _gc_start = time.time()
    else:
        # pyre-fixme[6]: Expected `float` for 1st param but got `Optional[float]`.
        duration = time.time() - _gc_start
        _gc_start = None

        if node_stats_service.node is not None:
            # pyre-fixme[6]: Expected `int` for 2nd param but got `float`.
            node_stats_service.log_gc_duration(info["generation"], duration)
        gen0, gen1, gen2 = gc.get_count()
        if duration >= constants.GC_DURATION_WARN_THRESHOLD:
            logger.statistics(
                {
                    "type": "GcDurationExceededWarningThreshold",
                    "start_time": datetime.fromtimestamp(time.time()),
                    "duration": duration,
                    "generation": info["generation"],
                    "collected": info["collected"],
                    "uncollectable": info["uncollectable"],
                    "total_uncollectable": len(gc.garbage),
                    "sizes": {"generation0": gen0, "generation1": gen1, "generation2": gen2},
                }
            )
