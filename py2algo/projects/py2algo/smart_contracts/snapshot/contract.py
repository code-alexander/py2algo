# pyright: reportMissingModuleSource=false

from algopy import Account, ARC4Contract, Asset, Global, UInt64, arc4, itxn

# class Snapshot(arc4.Struct):
#     at_round: arc4.UInt64
#     at_time: arc4.UInt64
#     asset_id: arc4.UInt64
#     balance: arc4.UInt64


class Snapshot(ARC4Contract):
    """A contract that takes snapshots of account balances."""

    @arc4.abimethod
    def create_snapshot(self, account: Account, asset: Asset) -> UInt64:
        """Mints an NFT with a snapshot of the account's balance of the asset.

        Args:
            account (Account): The account to snapshot.
            asset (Asset): The asset to snapshot the balance of.

        Returns:
            UInt64: The snapshot NFT asset ID.
        """
        balance = asset.balance(account) if asset else account.balance
        snapshot = (
            arc4.UInt64(Global.round).bytes
            + arc4.UInt64(Global.latest_timestamp).bytes
            + arc4.UInt64(asset.id).bytes
            + arc4.UInt64(balance).bytes
        )
        return (
            itxn.AssetConfig(
                total=1,
                decimals=0,
                asset_name="SNAPSHOT",
                unit_name=arc4.UInt64(asset.id).bytes,
                metadata_hash=snapshot,
                reserve=account,
                fee=0,
            )
            .submit()
            .created_asset.id
        )


# account.balance(asset)

# arc4.UInt64(account.balance(asset)).bytes
