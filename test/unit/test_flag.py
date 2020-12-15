from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.utils.flag_enum import Flag, FlagCollection


class TestEnumItem(Flag):
    pass


class TestEnum(FlagCollection):
    VALUE1 = TestEnumItem()
    VALUE2 = TestEnumItem()
    VALUE3 = TestEnumItem()
    VALUE4 = TestEnumItem()


TestEnum.init(TestEnumItem)


class TestEnumItem2(Flag):
    pass


class TestEnum2(FlagCollection):
    VALUE1 = TestEnumItem2()
    VALUE2 = TestEnumItem2()
    VALUE3 = TestEnumItem2()
    VALUE4 = TestEnumItem2()


TestEnum2.init(TestEnumItem2)


class FlagEnumTest(AbstractTestCase):

    def test_auto_assigned_values(self):
        self.assertTrue(4, len(TestEnumItem.names_map))

        # Verify that generated values do not overlap
        for item1 in TestEnumItem.names_map:
            for item2 in TestEnumItem.names_map:
                if item1 != item2:
                    self.assertFalse(item1 in item2)
                else:
                    self.assertTrue(item1 in item2)

        # Verify that values are generate uniquely within each enum
        self.assertTrue(TestEnum.VALUE1.value, TestEnum2.VALUE1.value)
        self.assertTrue(TestEnum.VALUE2.value, TestEnum2.VALUE2.value)
        self.assertTrue(TestEnum.VALUE3.value, TestEnum2.VALUE3.value)
        self.assertTrue(TestEnum.VALUE4.value, TestEnum2.VALUE4.value)

    def test_flag_contains(self):
        v1 = TestEnum.VALUE1
        v2 = TestEnum.VALUE2
        v3 = TestEnum.VALUE3
        v4 = TestEnum.VALUE4

        self.assertTrue(TestEnum.VALUE1 in v1)
        self.assertFalse(TestEnum.VALUE2 in v1)
        self.assertFalse(v2 in v1)
        self.assertFalse(v3 in v1)
        self.assertFalse(v4 in v1)

        self.assertTrue(v1 in v1 | v2)
        self.assertFalse(v1 in v1 & v2)

        self.assertTrue(v1 in TestEnum.VALUE1 | TestEnum.VALUE2 | TestEnum.VALUE3 | TestEnum.VALUE4)
        self.assertTrue(v1 not in TestEnum.VALUE1 & TestEnum.VALUE2 & TestEnum.VALUE3 & TestEnum.VALUE4)

    def test_repr(self):
        self.assertTrue("VALUE1", str(TestEnum.VALUE1))
        self.assertTrue("VALUE2", str(TestEnum.VALUE2))
        self.assertTrue("VALUE3", str(TestEnum.VALUE3))
        self.assertTrue("VALUE4", str(TestEnum.VALUE4))

        self.assertTrue("VALUE1|VALUE2", str(TestEnum.VALUE1 | TestEnum.VALUE2))
        self.assertTrue("VALUE1|VALUE2|VALUE3|VALUE4",
                        str(TestEnum.VALUE1 | TestEnum.VALUE2 | TestEnum.VALUE3 | TestEnum.VALUE4))

    def test_invert(self):
        v1 = TestEnum.VALUE1

        inverted_v1 = ~v1

        self.assertFalse(TestEnum.VALUE1 in inverted_v1)
        self.assertTrue(TestEnum.VALUE2 in inverted_v1)
        self.assertTrue(TestEnum.VALUE3 in inverted_v1)
        self.assertTrue(TestEnum.VALUE4 in inverted_v1)
        self.assertTrue("VALUE2|VALUE3|VALUE4", str(inverted_v1))
