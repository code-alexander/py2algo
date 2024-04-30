# pyright: reportMissingModuleSource=false
from typing import TypeAlias

from algopy import (
    Account,
    ARC4Contract,
    Asset,
    Global,
    OnCompleteAction,
    String,
    Txn,
    UInt64,
    arc4,
    gtxn,
    itxn,
    op,
    subroutine,
)

Backer: TypeAlias = Account
Vault: TypeAlias = Account
MaybeVault: TypeAlias = Account  # Vault account or the zero address


class VaultFactory(ARC4Contract):
    """A contract that creates an account and rekeys it to the sender."""

    @arc4.abimethod(create="require", allow_actions=[OnCompleteAction.DeleteApplication])
    def new(self) -> arc4.Address:
        """Creates a new account and rekeys it to the sender.

        Returns:
            arc4.Address: The vault address.
        """
        return arc4.Address(itxn.Payment(receiver=Txn.sender, rekey_to=Txn.sender, fee=0).submit().sender)


# Compiled TEAL code for the VaultFactory contract
VAULT_FACTORY_APPROVAL = b'\n \x01\x01\x80\x04V\x1d/\xea6\x1a\x00\x8e\x01\x00\x01\x001\x19\x81\x05\x12D1\x18\x14D\x88\x00\x0b\x80\x04\x15\x1f|uLP\xb0"C\x8a\x00\x01\xb11\x00I\x81\x00\xb2\x01\xb2 \xb2\x07"\xb2\x10\xb3\xb4\x00\x89'
VAULT_FACTORY_CLEAR = b"\n\x81\x01C"


@subroutine
def pay_from(sender: Account, /, *, to: Account, amount: UInt64) -> None:
    """Makes a payment from the sender to the receiver.

    Args:
        sender (Account): The account to send the payment from.
        to (Account): The account to send the payment to.
        amount (UInt64): The amount of MicroAlgos to pay to the receiver.
    """
    itxn.Payment(
        sender=sender,
        receiver=to,
        amount=amount,
        fee=0,
    ).submit()


@subroutine
def create_vault(backer: Backer) -> Vault:
    """Creates a new vault account for a backer and saves it in box storage.

    Args:
        backer (Backer): The backer account.

    Returns:
        Vault: The vault account.
    """
    # Call the vault factory contract to create a new vault
    address, _txn = arc4.abi_call(
        VaultFactory.new,
        approval_program=VAULT_FACTORY_APPROVAL,
        clear_state_program=VAULT_FACTORY_CLEAR,
        on_completion=OnCompleteAction.DeleteApplication,
        fee=0,
    )
    vault = Account(address.bytes)

    # Save (backer, vault) pair in box storage
    op.Box.put(backer.bytes, vault.bytes)

    return vault


@subroutine
def find_vault(backer: Backer) -> MaybeVault:
    """Finds the backer's vault, if it exists.

    Args:
        backer (Backer): The backer to find the vault for.

    Returns:
        MaybeVault: The vault if found, else the zero address.
    """
    maybe_vault, exists = op.Box.get(backer.bytes)
    return Account(maybe_vault) if exists else Global.zero_address


@subroutine
def close(backer: Backer, vault: Vault, to: Account) -> UInt64:
    """Closes the vault and transfers its balance to the receiver.

    Args:
        backer (Backer): The backer to close the vault for.
        vault (Vault): The vault to close.
        to (Account): The account to transfer the funds to.

    Returns:
        UInt64: The amount transferred to the receiver.
    """
    _deleted = op.Box.delete(backer.bytes)
    return (
        itxn.Payment(
            sender=vault,
            receiver=to,
            amount=vault.balance,
            close_remainder_to=to,
            fee=0,
        )
        .submit()
        .amount
    )


@subroutine
def mint_certificate(investor: Account, invested_amount: UInt64) -> Asset:
    """Mints an NFT to certify an investor's participation in the funding round.

    Args:
        investor (Account): The investor's account.
        invested_amount (UInt64): The amount they inested.

    Returns:
        Asset: The certificate asset.
    """
    return (
        itxn.AssetConfig(
            total=1,
            decimals=0,
            asset_name="CERT",
            unit_name=arc4.UInt64(invested_amount).bytes,
            reserve=investor,  # Has no authority in the Algorand protocol
            fee=0,
        )
        .submit()
        .created_asset
    )


class VentureFunding(ARC4Contract):
    """A smart contract for decentralised venture funding."""

    @arc4.abimethod(create="require")
    def new_project(
        self,
        project_name: String,
        funding_target: UInt64,
        funding_deadline: UInt64,
        minimum_pledge: UInt64,
    ) -> None:
        """Creates a new venture funding project.

        Args:
            project_name (String): The name of the project.
            funding_target (UInt64): The funding target amount in MicroAlgos.
            funding_deadline (UInt64): The round that the target amount must be raised by, in order for the project to access the funds.
            minimum_pledge (UInt64): The minimum amount of MicroAlgos that a backer can pledge to the project.
        """
        assert funding_deadline > Global.round, "Funding deadline must be in the future"
        assert funding_target > minimum_pledge, "Funding target must be > the minimum pledge"
        assert minimum_pledge >= Global.min_balance, "Minimum pledge must be >= the minimum account balance"

        self.project_name = project_name
        self.funding_target = funding_target
        self.funding_deadline = funding_deadline
        self.minimum_pledge = minimum_pledge
        self.pledged_amount = UInt64(0)

    @arc4.abimethod
    def pledge(self, payment: gtxn.PaymentTransaction) -> UInt64:
        """Makes a pledge to the project.

        Args:
            payment (gtxn.PaymentTransaction): The payment transaction transferring the pledged amount to the contract.

        Returns:
            UInt64: The total amount pledged by the backer.
        """
        assert Global.round < self.funding_deadline, "The funding round has closed"
        assert payment.receiver == Global.current_application_address, "Payment receiver must be the app address"
        assert payment.amount >= self.minimum_pledge, "Payment amount must >= the minimum pledge"

        vault = find_vault(payment.sender) or create_vault(payment.sender)

        # Pay the pledge to the vault
        pay_from(Global.current_application_address, to=vault, amount=payment.amount)

        self.pledged_amount += payment.amount

        return vault.balance

    @arc4.abimethod
    def claim_refund(self) -> UInt64:
        """Refunds a backer if the funding deadline has passed and the target has not been met.

        Returns:
            UInt64: The amount of MicroAlgos refunded.
        """
        assert Global.round >= self.funding_deadline, "Funding deadline has not passed"
        assert self.pledged_amount < self.funding_target, "Funding target has been met"

        vault = find_vault(Txn.sender)
        assert vault, "Vault not found"

        return close(Txn.sender, vault, to=Txn.sender)

    @arc4.abimethod
    def withdraw_funds_from(self, backer: arc4.Address) -> tuple[UInt64, UInt64]:
        """Closes the backer's vault and transfers its balance to the application creator.

        Args:
            backer (arc4.Address): The backer's address.

        Returns:
            tuple[UInt64, UInt64]: The total amount of MicroAlgos withdrawn and the asset ID of the certificate minted.
        """
        assert Global.round >= self.funding_deadline, "Funding deadline has not passed"
        assert self.pledged_amount >= self.funding_target, "Funding target has not been met"

        backer_account = Account(backer.bytes)
        vault = find_vault(backer_account)
        assert vault, "Vault not found"

        invested_amount = close(backer_account, vault, to=Global.creator_address)
        certificate = mint_certificate(backer_account, invested_amount)
        return invested_amount, certificate.id

    @arc4.abimethod
    def claim_certificate(self, certificate: Asset) -> None:
        """Transfers the certificate to the investor.

        Args:
            certificate (Asset): The certificate asset to withdraw.
        """
        assert Global.round >= self.funding_deadline, "Funding deadline has not passed"
        assert self.pledged_amount >= self.funding_target, "Funding target has not been met"

        itxn.AssetTransfer(
            xfer_asset=certificate,
            asset_receiver=certificate.reserve,
            asset_amount=1,
            fee=0,
        ).submit()
