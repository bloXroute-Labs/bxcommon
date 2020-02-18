import time

from bxutils.logging import CustomLogger


def log_operation_duration(logger: CustomLogger, operation_name: str, start_time: float, duration_warn_threshold: float,
                           **kwargs):
    duration = time.time() - start_time
    logger.trace("Performance: {} took {:.3f} s to execute. {}", operation_name, duration, kwargs)

    if duration > duration_warn_threshold:
        logger.debug("Performance Warning: {} took over defined threshold ({} s) to execute, {:.3f}s. {}",
                     operation_name, duration_warn_threshold, duration, kwargs)
