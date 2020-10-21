from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.utils.limited_size_dict import LimitedSizeDict


class LimitedSizeDictTest(AbstractTestCase):

    def setUp(self) -> None:
        self.sut = LimitedSizeDict(5)
        for i in range(5):
            self.sut.add(i, str(i))

    def test_getting_items(self):
        for i in range(5):
            self.assertEqual(str(i), self.sut[i])

    def test_expiring_items(self):
        self.sut.add(6, "6")

        self.assertEqual(5, len(self.sut))
        self.assertNotIn(0, self.sut)
        self.assertEqual("1", self.sut[1])

    def test_overfilled_dict(self):
        for i in range(5, 10):
            self.sut.contents[i] = str(i)
            self.sut.key_tracker.append(i)

        self.sut.add(10, "10")
        self.assertEqual(5, len(self.sut))

        for i in range(6):
            self.assertNotIn(i, self.sut)

        for i in range(7, 11):
            self.assertEqual(str(i), self.sut[i])
