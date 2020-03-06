import time
from datetime import datetime

from bxutils import logging
from bxutils.logging import CustomLogger

logger = logging.get_logger(__name__)


def log_operation_duration(
    stats_logger: CustomLogger,
    operation_name: str,
    start_time: float,
    duration_warn_threshold: float,
    **kwargs
):
    duration = time.time() - start_time
    logger.trace("Performance: {} took {:.3f} s to execute. {}", operation_name, duration, kwargs)

    if duration > duration_warn_threshold:
        logger.debug(
            "Performance Warning: {} took over defined threshold ({} s) to execute, {:.3f}s. {}",
            operation_name,
            duration_warn_threshold,
            duration,
            kwargs,
        )

        stats_logger.statistics(
            {
                "type": "OperationDurationExceededWarningThreshold",
                "start_time": datetime.utcnow(),
                "operation": operation_name,
                "duration": duration,
                "duration_warn_threshold": duration_warn_threshold,
                "data": {k: str(v) for (k, v) in kwargs.items()},
            }
        )
