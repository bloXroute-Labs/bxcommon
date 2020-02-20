from datatime import datetime
import time

from bxutils.logging import CustomLogger


def log_operation_duration(logger: CustomLogger, operation_name: str, start_time: float, duration_warn_threshold: float,
                           **kwargs):
    duration = time.time() - start_time
    logger.trace("Performance: {} took {:.3f} s to execute. {}", operation_name, duration, kwargs)

    if duration > duration_warn_threshold:

        logger.statistics(
            {
                "type": "MessageHandling",
                "start_time": datetime.utcnow(),
                "operation": operation_name,
                "duration": duration,
                "duration_warn_threshold": duration_warn_threshold,
                "data": kwargs
            }
        )
