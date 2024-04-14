# pyright: reportMissingModuleSource=false
from typing import TypeAlias

from algopy import ARC4Contract, String, UInt64, arc4, uenumerate, urange

UInt64Array: TypeAlias = arc4.DynamicArray[arc4.UInt64]


class Iteration(ARC4Contract):
    """A contract demonstrating iteration methods in algopy."""

    @arc4.abimethod
    def sum(self, array: UInt64Array) -> UInt64:
        """Sums an array of numbers.

        Args:
            array (UInt64Array): The array to sum.

        Returns:
            UInt64: The sum of the array.
        """
        total = UInt64(0)
        for n in array:
            total += n.native
        return total

    @arc4.abimethod
    def first_even(self, array: UInt64Array) -> UInt64:
        """Returns the first even number in the array.

        Defaults to zero.

        Args:
            array (UInt64Array): The array to search.

        Returns:
            UInt64: The first even number.
        """
        for n in array:
            if n.native % 2 == 0:
                return n.native
        return UInt64(0)

    @arc4.abimethod
    def last_even_index(self, array: UInt64Array) -> UInt64:
        """Returns the index of the last even number in the array.

        Defaults to zero.

        Args:
            array (UInt64Array): The array to search.

        Returns:
            UInt64: The index of the last even number.
        """
        for i, n in reversed(uenumerate(array)):
            if n.native % 2 == 0:
                return i
        return UInt64(0)

    @arc4.abimethod
    def repeat(self, string: arc4.String, times: UInt64) -> String:
        """Repeats a string a number of times.

        Args:
            string (arc4.String): The string to repeat.
            times (UInt64): The number of times to repeat the string.

        Returns:
            String: The repeated string.
        """
        result = String()
        for _i in urange(times):
            result += string.native
        return result

    @arc4.abimethod
    def fibonacci(self, n: UInt64) -> UInt64:
        """Returns the nth Fibonacci number.

        Args:
            n (UInt64): The index of the Fibonacci number to return.

        Returns:
            UInt64: The nth Fibonacci number.
        """
        return n if n <= 1 else self.fibonacci(n - 1) + self.fibonacci(n - 2)

    