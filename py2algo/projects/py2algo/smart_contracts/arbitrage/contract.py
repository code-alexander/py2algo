# pyright: reportMissingModuleSource=false


from algopy import (
    Account,
    ARC4Contract,
    Asset,
    Global,
    Txn,
    UInt64,
    arc4,
    gtxn,
    subroutine,
)


class BalanceProtector(ARC4Contract):
    """Fails a group of transactions if the owner's account balance ends lower than it starts."""

    @arc4.abimethod(create="require")
    def new(self, owner: Account) -> None:
        self.owner = owner
        self.asset = Asset(0)
        self.starting_balance = UInt64(0)

    @subroutine
    def balance(self) -> UInt64:
        """Fetches the owner's balance of the asset (ASA or Algo).

        Returns:
            UInt64: The owner's balance.
        """
        return self.asset.balance(self.owner) if self.asset else self.owner.balance

    @arc4.abimethod
    def take_snapshot(self, asset: Asset) -> UInt64:
        """Stores a snapshot of the owner's balance in the contract's global state.

        Args:
            asset (Asset): The asset to snapshot the balance of.

        Returns:
            UInt64: The round the snapshot was taken in.
        """
        assert Txn.sender == self.owner, "Only the owner can call this method."
        assert Txn.group_index == 0, "Transaction must be first in group."
        assert (
            gtxn.ApplicationCallTransaction(Global.group_size - 1).app_id == Global.current_application_id
        ), "Last transaction in group must be a call to this application."

        self.asset = asset
        self.starting_balance = self.balance()
        return Global.round

    @arc4.abimethod
    def protect(self) -> UInt64:
        """Fails if the owner's balance is lower than it was at the snapshot round.

        Returns:
            UInt64: The balance delta.
        """
        assert Txn.sender == self.owner, "Only the owner can call this method."
        assert Txn.group_index == Global.group_size - 1, "Transaction must be last in group."
        assert (
            gtxn.ApplicationCallTransaction(0).app_id == Global.current_application_id
        ), "First transaction in group must be a call to this application."

        # Will cause an error (would result in negative)
        # If the balance is less than the starting balance
        return self.balance() - Txn.fee - self.starting_balance
