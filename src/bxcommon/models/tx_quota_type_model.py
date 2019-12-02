from enum import IntFlag

# IntFlag allows comparison with ints, which is not as strict as Flag, but allows easier unit testing.
class TxQuotaType(IntFlag):
    NONE = 0
    FREE_DAILY_QUOTA = 1
    PAID_DAILY_QUOTA = 2

    def __str__(self):
        return self.name
