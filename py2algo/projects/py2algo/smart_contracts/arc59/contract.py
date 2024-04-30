# pyright: reportMissingModuleSource=false
from typing import TypeAlias

from algopy import Account, ARC4Contract, Asset, Global, OnCompleteAction, Txn, UInt64, arc4, gtxn, itxn, op, subroutine


class VaultFactory(ARC4Contract):
    """A contract that creates an account and rekeys it to the sender."""

    @arc4.abimethod(create="require", allow_actions=[OnCompleteAction.DeleteApplication])
    def new(self) -> arc4.Address:
        """Creates a new application account and rekeys it to the sender.

        Returns:
            arc4.Address: The address of the new application account.
        """
        itxn.Payment(receiver=Txn.sender, rekey_to=Txn.sender).submit()
        return arc4.Address(Global.current_application_address)


@subroutine
def opt_in(account: Account, asset: Asset) -> None:
    """Opts an account in to an asset.

    Args:
        account (Account): The account to opt in.
        asset (Asset): The asset to opt in to.
    """
    itxn.AssetTransfer(
        xfer_asset=asset,
        asset_receiver=account,
        asset_amount=0,
        fee=0,
    ).submit()


@subroutine
def transfer_asset_to(receiver: Account, /, *, asset: Asset, amount: UInt64) -> None:
    """Transfers an asset to the receiver.

    Args:
        receiver (Account): The account to transfer the asset to.
        asset (Asset): The asset to transfer.
        amount (UInt64): The amount of the asset to transfer.
    """
    itxn.AssetTransfer(
        xfer_asset=asset,
        asset_receiver=receiver,
        asset_amount=amount,
        fee=0,
    ).submit()


@subroutine
def close_asset_remainder_from(sender: Account, /, *, to: Account, asset: Asset) -> None:
    """Transfers the remaining balance of an asset to the receiver, and opts out of the asset.

    Args:
        sender (Account): The asset sender.
        to (Account): The asset receiver.
        asset (Asset): The asset to transfer.
    """
    itxn.AssetTransfer(xfer_asset=asset, sender=sender, asset_receiver=to, asset_close_to=to, fee=0).submit()


MaybeVault: TypeAlias = Account  # Vault account or the zero address


@subroutine
def find_vault(receiver: arc4.Address) -> MaybeVault:
    maybe_vault, _exists = op.Box.get(receiver.bytes)
    return Account(maybe_vault)


@subroutine
def pay_from(sender: Account, /, *, to: Account, amount: UInt64) -> None:
    """Makes a payment from one account to another.

    Args:
        sender (Account): The payment sender.
        to (Account): The payment receiver.
        amount (UInt64): The amount of MicroAlgos to pay.
    """
    itxn.Payment(
        sender=sender,
        receiver=to,
        amount=amount,
        fee=0,
    ).submit()


@subroutine
def ensure_funded(account: Account, min_balance: UInt64) -> None:
    """Tops up an account with the minimum balance if it is below the threshold.

    Args:
        account (Account): The account to top up.
        min_balance (UInt64): The minimum balance the account must have.
    """
    if account.balance < min_balance:
        pay_from(Global.current_application_address, to=account, amount=min_balance)


@subroutine
def create_vault(receiver: arc4.Address) -> Account:
    """Creates a new vault account, funds it with the minimum balance, and puts the address in box storage.

    Args:
        receiver (arc4.Address): The receiver address.

    Returns:
        Account: The vault account.
    """
    vault, _txn = arc4.abi_call(VaultFactory.new, on_completion=OnCompleteAction.DeleteApplication)
    pay_from(Global.current_application_address, to=Account(vault.bytes), amount=Global.min_balance)
    op.Box.put(receiver.bytes, vault.bytes)
    return Account(vault.bytes)


class Router(ARC4Contract):
    """A router contract that enables the transfer of assets to any address."""

    @arc4.abimethod
    def opt_router_in(self, asset_id: UInt64) -> None:
        """Opts the router in to the asset.

        This is required before the app can be used to send the asset to a receiver.

        Args:
            asset_id (UInt64): The ID of the asset to opt in to.
        """
        opt_in(Global.current_application_address, Asset(asset_id))

    @arc4.abimethod
    def send_asset(self, axfer: gtxn.AssetTransferTransaction, receiver: arc4.Address) -> arc4.Address:
        """Sends an asset from the application account to the receiver, or to their vault.

        Args:
            axfer (gtxn.AssetTransferTransaction): The transaction transferring the asset to the router app.
            receiver (arc4.Address): The intended asset receiver.

        Returns:
            arc4.Address: The address the asset was sent to.
        """
        assert (
            axfer.asset_receiver == Global.current_application_address
        ), "`axfer.asset_receiver` must be the router app address"
        assert (
            Account(receiver.bytes).auth_address != Global.current_application_address
        ), "`receiver` must not be a vault or the router app address"

        # If the receiver is opted in, send directly to their account
        if Account(receiver.bytes).is_opted_in(axfer.xfer_asset):
            transfer_asset_to(Account(receiver.bytes), asset=axfer.xfer_asset, amount=axfer.asset_amount)
            return receiver

        vault = find_vault(receiver) or create_vault(receiver)

        if not vault.is_opted_in(axfer.xfer_asset):
            ensure_funded(vault, vault.min_balance + Global.asset_opt_in_min_balance)
            opt_in(vault, axfer.xfer_asset)

        transfer_asset_to(vault, asset=axfer.xfer_asset, amount=axfer.asset_amount)

        return arc4.Address(vault)

    @arc4.abimethod
    def claim_asset(self, asset_id: UInt64) -> None:
        """Withdraws the total balance of an asset from a vault.

        The transaction must be sent by the receiver that owns the vault.

        Args:
            asset_id (UInt64): The ID of the asset to withdraw.
        """
        vault = find_vault(arc4.Address(Txn.sender))
        assert vault, "Vault not found for transaction sender"

        close_asset_remainder_from(vault, to=Txn.sender, asset=Asset(asset_id))
        pay_from(vault, to=Global.current_application_address, amount=Global.asset_opt_in_min_balance)
