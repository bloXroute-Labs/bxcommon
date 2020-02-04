import time
from datetime import datetime

from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.utils.concurrency.thread_pool import ThreadPool


class ThreadPoolTest(AbstractTestCase):

    def setUp(self):
        super().setUp()
        self.workers = 5
        self.thread_pool = ThreadPool(self.workers, "test_thread_pool")
        self.thread_pool.start()

    def tearDown(self) -> None:
        super().tearDown()
        self.thread_pool.stop()
        self.thread_pool.close()

    def test_single_submit_success(self):

        def my_test_callback(a, b, c):
            return a, b, c

        a = 1
        b = 2
        c = 3
        future = self.thread_pool.submit(my_test_callback, a, b, c=c)
        result = future.result()
        self.assertEqual((a, b, c), result)

    def test_single_submit_failed(self):
        def my_test_callback():
            raise RuntimeError("My error")

        future = self.thread_pool.submit(my_test_callback)
        self.assertRaises(RuntimeError, future.result)

    def test_multiple_submit_success(self):

        def run_with_delay(delay: float) -> datetime:
            time.sleep(delay)
            return datetime.now()

        very_long_delay = 0.5
        long_delay = 0.1
        short_delay = 0.01

        very_long = self.thread_pool.submit(run_with_delay, very_long_delay)
        long = self.thread_pool.submit(run_with_delay, long_delay)
        short = self.thread_pool.submit(run_with_delay, short_delay)
        self.assertGreater(very_long.result(), long.result())
        self.assertGreater(long.result(), short.result())

    def test_above_worker_count(self):
        futures = []
        for _ in range(2 * self.workers):
            futures.append(
                self.thread_pool.submit(time.sleep, 0.2)
            )
        for future in futures:
            future.result()

