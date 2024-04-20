# pyright: reportMissingModuleSource=false
from algopy import ARC4Contract, UInt64, arc4, urange


class Quiz(ARC4Contract):
    """Quiz questions for the Algorand Foundation."""

    @arc4.abimethod
    def question_one(self) -> UInt64:
        """What value is returned from this method?"""
        total = UInt64(0)
        for i in urange(10):
            if i % 2 == 0:
                total += i
        return total
