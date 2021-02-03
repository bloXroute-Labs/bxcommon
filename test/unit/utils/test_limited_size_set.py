from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.utils.limited_size_set import LimitedSizeSet


class LimitedSizeSetTest(AbstractTestCase):

    def setUp(self) -> None:
        self.sut = LimitedSizeSet(5)
        for i in range(5):
            self.sut.add(i)

    def test_contains(self):
        for i in range(5):
            self.assertIn(i, self.sut)

    def test_expiring_items(self):
        self.sut.add(6)

        self.assertEqual(5, len(self.sut))
        self.assertNotIn(0, self.sut)
        self.assertIn(1, self.sut)

    def test_overfilled_set(self):
        for i in range(5, 10):
            self.sut.add(i)

        self.sut.add(10)
        self.assertEqual(5, len(self.sut))

        for i in range(6):
            self.assertNotIn(i, self.sut)

        for i in range(7, 11):
            self.assertIn(i, self.sut)

    def test_set_handles_duplicate_items(self):
        for i in range(0, 5):
            self.sut.add(i)

        self.sut.add(4)
        self.assertEqual(5, len(self.sut))
        self.assertIn(0, self.sut)
