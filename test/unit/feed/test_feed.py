from typing import Any

from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.test_utils.helpers import async_test
from bxcommon.feed.feed import Feed


class TestFeed(Feed[Any, Any]):
    def __init__(self):
        super().__init__("testfeed")
        self.expensive_serialization_count = 0

    def serialize(self, raw_message: int) -> int:
        self.expensive_serialization_count += 1
        return raw_message


class FeedTest(AbstractTestCase):

    @async_test
    async def test_serialization_avoided_if_no_subscribers(self):
        test_feed = TestFeed()

        test_feed.publish(1)
        self.assertEqual(0, test_feed.expensive_serialization_count)

        subscriber = test_feed.subscribe({})
        test_feed.publish(2)
        self.assertEqual(1, test_feed.expensive_serialization_count)
        self.assertEqual(2, await subscriber.receive())

    @async_test
    async def test_same_feed_published_if_same_options(self):
        test_feed = TestFeed()

        subscriber = test_feed.subscribe({"include": ["foo"]})
        same_options_subscriber = test_feed.subscribe({"include": ["foo"]})
        diff_options_subscriber = test_feed.subscribe({"include": ["foo", "bar"]})

        test_feed.publish({"foo": "bar", "bar": "baz"})

        subscriber_one_content = await subscriber.receive()
        subscriber_same_content = await same_options_subscriber.receive()
        subscriber_diff_content = await diff_options_subscriber.receive()

        self.assertEqual(subscriber_one_content, subscriber_same_content)
        self.assertTrue(subscriber_one_content is subscriber_same_content)
        self.assertNotEqual(subscriber_diff_content, subscriber_one_content)
