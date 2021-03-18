import sys
import gc
import time
from datetime import datetime
from typing import Dict, Any, Optional
from types import FrameType

from bxcommon import constants
from bxcommon.utils.stats.node_statistics_service import node_stats_service
from bxutils import logging
from bxutils.logging import LogRecordType

logger = logging.get_logger(LogRecordType.GarbageCollection)

_gc_start: Optional[float] = None


def gc_callback(phase: str, info: Dict[str, Any]):
    # pylint: disable=global-statement
    global _gc_start
    gc_start = _gc_start

    if phase == "start" and gc_start is None:
        _gc_start = time.time()
    elif gc_start is not None:
        duration = time.time() - gc_start
        _gc_start = None

        if node_stats_service.node is not None:
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
    else:
        logger.debug("invalid state when attempting to track GC state skip")


# helper functions in case we need to find cyclic references.
# gc.set_debug(gc.DEBUG_SAVEALL)
# gc.collect()
# objs = gc.garbage
# for obj in objs:
#     try:
#         sys.stdout.write("Examining: %r\n" % obj)
#         recurse(objs, obj, obj, {}, [])
#     except Exception as e:
#         pass
def print_path(path):
    for i, step in enumerate(path):
        # next "wraps around"
        next = path[(i + 1) % len(path)]

        sys.stdout.write("   %s -- " % str(type(step)))
        if isinstance(step, dict):
            for key, val in step.items():
                if val is next:
                    sys.stdout.write("[%s]" % repr(key))
                    break
                if key is next:
                    sys.stdout.write("[key] = %s" % repr(val))
                    break
        elif isinstance(step, list):
            sys.stdout.write("[%d]" % step.index(next))
        elif isinstance(step, tuple):
            sys.stdout.write("[%d]" % list(step).index(next))
        else:
            sys.stdout.write(repr(step))
        sys.stdout.write(" ->\n")
    sys.stdout.write("\n")


def recurse(objs, obj, start, all, current_path):
    # if show_progress:
    #     outstream.write("%d\r" % len(all))

    all[id(obj)] = None

    referents = gc.get_referents(obj)
    for referent in referents:
        # If we've found our way back to the start, this is
        # a cycle, so print it out
        if referent is start:
            print_path(current_path)

        # Don't go back through the original list of objects, or
        # through temporary references to the object, since those
        # are just an artifact of the cycle detector itself.
        elif referent is objs or isinstance(referent, FrameType):
            continue

        # We haven't seen this object before, so recurse
        elif id(referent) not in all:
            recurse(objs, referent, start, all, current_path + [obj])
