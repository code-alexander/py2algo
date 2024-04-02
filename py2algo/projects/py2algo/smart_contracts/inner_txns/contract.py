# pyright: reportMissingModuleSource=false

from algopy import ARC4Contract, Asset, Bytes, Global, Txn, UInt64, arc4, itxn, subroutine


@subroutine
def itoa(n: UInt64, /) -> Bytes:
    """Convert an integer to ASCII bytes.

    Args:
        n (UInt64): The integer.

    Returns:
        Bytes: The ASCII bytes.
    """
    digits = Bytes(b"0123456789")
    acc = Bytes()
    while n > 0:
        acc = digits[n % 10] + acc
        n //= 10
    return acc or Bytes(b"0")


class Inner(ARC4Contract):
    """A contract demonstrating inner transactions in algopy."""

    def __init__(self) -> None:
        self.counter = UInt64(0)

    @arc4.abimethod
    def mint_nft(self) -> UInt64:
        """Mints an NFT.

        Returns:
            UInt64: The asset ID of the NFT minted.
        """
        self.counter += 1
        return (
            itxn.AssetConfig(total=1, decimals=0, asset_name="DOG", unit_name=b"DOG_" + itoa(self.counter), fee=0)
            .submit()
            .created_asset.id
        )

    @arc4.abimethod
    def opt_in(self, asset: Asset) -> None:
        """Opts the application account in to receive an asset.

        Args:
            asset (Asset): The asset to opt in to.
        """
        itxn.AssetTransfer(
            asset_receiver=Global.current_application_address,
            xfer_asset=asset,
            fee=0,
        ).submit()

    @arc4.abimethod
    def withdraw(self, amount: UInt64) -> None:
        """Transfers Algos to the application creator's account.

        Args:
            amount (UInt64): The amount of MicroAlgos to withdraw.
        """
        assert Txn.sender == Global.creator_address, "Only the creator can withdraw"
        itxn.Payment(receiver=Global.creator_address, amount=amount, fee=0).submit()
