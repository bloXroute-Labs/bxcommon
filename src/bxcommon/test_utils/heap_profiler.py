import sys
import time

from pympler import tracker, muppy, summary

from bxcommon.constants import PROFILING


##
# The Memory Profiling Interface
##
class HeapProfiler(object):
    PROFILE_START = 0  # Time to start profiling
    PROFILE_INTERVAL = 300  # Profiling interval (in seconds)

    def __init__(self):
        print "constants.PROFILING:"
        print PROFILING

        if not PROFILING:
            self.profiling = False
            return

        print "constants.PROFILING:"
        print PROFILING
        self.profiling = True
        self.filename = ""
        self.last_rotation_time = time.time()

        tracker.SummaryTracker()

    def dump_profile(self):
        logger.log_debug("Dumping heap profile!")

        # Assumption is that no one else will be printing while profiling is happening
        self.filename = "profiler-" + time.strftime("%Y-%m-%d-%H:%M:%S+0000", time.gmtime()) + ".prof"

        old_stdout = sys.stdout
        sys.stdout = open(self.filename, "a+")
        print "################# BEGIN NEW HEAP SNAPSHOT #################"
        all_objects = muppy.get_objects()
        print "Printing diff at time: " + time.strftime("%Y-%m-%d-%H:%M:%S+0000", time.gmtime())
        sum1 = summary.summarize(all_objects)
        summary.print_(sum1)
        print "Printing out all objects: "
        print "Index,Type, size"
        i = 0
        for obj in all_objects:
            print "{0},{1},{2}".format(i, type(obj), sys.getsizeof(obj))
            i += 1

        i = 0
        print "Index,Object"
        for obj in all_objects:
            print "{0},{1}".format(i, repr(obj))
            i += 1

        print "################## END NEW HEAP SNAPSHOT ##################"
        sys.stdout = old_stdout

        return self.PROFILE_INTERVAL
