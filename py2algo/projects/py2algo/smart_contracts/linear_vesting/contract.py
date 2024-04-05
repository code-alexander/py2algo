# pyright: reportMissingModuleSource=false
from algopy import Account, ARC4Contract, Global, UInt64, arc4, itxn


class Vesting(ARC4Contract):
    """A linear vesting contract."""

    @arc4.abimethod(create="require")
    def new(self, beneficiary: Account, start: UInt64, duration: UInt64) -> None:
        """Creates a new application.

        Args:
            beneficiary (Account): The account that will receive the vested funds.
            start (UInt64): The round at which the vesting begins.
            duration (UInt64): The number of rounds the vesting is distributed over.
        """
        self.beneficiary = beneficiary
        self.start = start
        self.duration = duration
        self.released = UInt64(0)

    @arc4.abimethod
    def calculate_vesting(self, *, allocation: UInt64, start: UInt64, duration: UInt64, at: UInt64) -> UInt64:
        """Calculates the vesting amount at a specific round.

        Args:
            allocation (UInt64): The total funds allocated for vesting.
            start (UInt64): The round at which the vesting begins.
            duration (UInt64): The number of rounds the vesting is distributed over.
            at (UInt64): The round that the vesting amount will be calculated 'as at'.

        Returns:
            UInt64: The vesting amount.
        """
        if at < start:
            return UInt64(0)
        if at >= start + duration:
            return allocation
        return allocation * (at - start) // duration

    @arc4.abimethod
    def release_funds(self) -> None:
        """Transfers vested funds to the benefiary's account."""
        vested = self.calculate_vesting(
            allocation=Global.current_application_address.balance + self.released,
            start=self.start,
            duration=self.duration,
            at=Global.round,
        )
        releaseable = vested - self.released
        assert releaseable, "No funds to release at the current round"
        self.released += itxn.Payment(receiver=self.beneficiary, amount=releaseable, fee=0).submit().amount
