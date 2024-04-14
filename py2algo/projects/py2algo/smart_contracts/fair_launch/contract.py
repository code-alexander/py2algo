# pyright: reportMissingModuleSource=false
from algopy import ARC4Contract, Asset, Bytes, Global, Txn, UInt64, arc4, itxn, op

TARGET_LIMIT = 2**64 - 1


class FairLaunch(ARC4Contract):
    """A contract for fairly launching an NFT project."""

    @arc4.abimethod(create="require")
    def new(
        self, *, genesis_hash: Bytes, minimum_balance: UInt64, zero_bits: UInt64, difficulty_halving_interval: UInt64
    ) -> None:
        """Creates a new application.

        Args:
            genesis_hash (Bytes): The value to use for the first hash.
            minimum_balance (UInt64): The minimum amount of MicroAlgos an account must have to claim an asset.
            zero_bits (UInt64): The maximum number of leading zero bits the target number can have.
            difficulty_halving_interval (UInt64): The number of rounds that elapse between each difficulty halving.
        """
        assert zero_bits < 64, "`zero_bits` must be < 64"

        self.previous_hash = genesis_hash
        self.minimum_balance = minimum_balance
        self.zero_bits = zero_bits
        self.difficulty_halving_interval = difficulty_halving_interval
        self.last_round = Global.round

    @arc4.abimethod
    def calculate_target(
        self, zero_bits: UInt64, difficulty_halving_interval: UInt64, last_round: UInt64, at_round: UInt64
    ) -> UInt64:
        """Calculate the target number that the hash must be less than or equal to.

        Args:
            zero_bits (UInt64): The maximum number of leading zero bits the target number can have.
            difficulty_halving_interval (UInt64): The number of rounds that elapse between each difficulty halving.
            last_round (UInt64): The last round an asset was released at.
            at_round (UInt64): The round that the target is calculated 'as at'.

        Returns:
            UInt64: The target number.
        """
        halvings = (at_round - last_round) // difficulty_halving_interval
        return UInt64(TARGET_LIMIT) if halvings > zero_bits else UInt64(TARGET_LIMIT) >> zero_bits - halvings

    @arc4.abimethod
    def claim(self, asset: Asset) -> None:
        """Transfers the requested asset to the claimant, if they are eligible to receive it.

        Args:
            asset (Asset): The requested asset.
        """
        assert Txn.sender.balance >= self.minimum_balance, "Sender's balance is below the minimum requirement"
        new_hash = op.sha256(Txn.sender.bytes + self.previous_hash)
        assert op.extract_uint64(new_hash, 0) < self.calculate_target(
            self.zero_bits, self.difficulty_halving_interval, self.last_round, Global.round
        )
        itxn.AssetTransfer(xfer_asset=asset, asset_amount=1, asset_receiver=Txn.sender, fee=0).submit()
        self.previous_hash = new_hash
        self.last_round = Global.round
