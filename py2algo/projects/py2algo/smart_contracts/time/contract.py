# pyright: reportMissingModuleSource=false

"""Credit to Howard Hinnant for the algorithm: https://howardhinnant.github.io/date_algorithms.html"""

from typing import TypeAlias

from algopy import (
    ARC4Contract,
    UInt64,
    arc4,
)

YearMonthDay: TypeAlias = tuple[UInt64, UInt64, UInt64]


class Time(ARC4Contract):
    """A contract that converts between Unix time and Gregorian time."""

    @arc4.abimethod
    def to_date(self, timestamp: UInt64) -> YearMonthDay:
        """Converts a Unix timestamp to a Gregorian date.

        Args:
            timestamp (UInt64): The Unix timestamp to convert.

        Returns:
            YearMonthDay: The Gregorian date as a (year, month, day) triple.
        """
        # Number of days since 1970-01-01
        z = timestamp // 86400
        # Shift the epoch from 1970-01-01 to 0000-03-01
        z += 719468
        era = z // 146097
        doe = z - era * 146097  # [0, 146096]
        yoe = (doe - doe // 1460 + doe // 36524 - doe // 146096) // 365  # [0, 399]
        y = yoe + era * 400
        doy = doe - (365 * yoe + yoe // 4 - yoe // 100)  # [0, 365]
        mp = (5 * doy + 2) // 153  # [0, 11]
        d = doy - (153 * mp + 2) // 5 + 1  # [1, 31]
        m = mp + 3 if mp < 10 else mp - 9  # [1, 12]
        return y + (UInt64(1) if m <= 2 else UInt64(0)), m, d
