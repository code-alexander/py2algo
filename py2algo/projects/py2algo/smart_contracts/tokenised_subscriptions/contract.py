# pyright: reportMissingModuleSource=false
from algopy import Account, ARC4Contract, Asset, Global, Txn, UInt64, arc4, gtxn, itxn, op


class TokenisedSubscriptions(ARC4Contract):
    """A contract for subscription payments using redeemable NFTs."""

    @arc4.abimethod
    def mint_tokens(
        self,
        initial_redeemer: Account,
        active_from: arc4.UInt64,
        payment_amount: arc4.UInt64,
        payment_frequency: arc4.UInt64,
        max_payments: arc4.UInt64,
    ) -> UInt64:
        """Creates

        Args:
            initial_redeemer (Account): _description_
            active_from (arc4.UInt64): _description_
            payment_amount (arc4.UInt64): _description_
            payment_frequency (arc4.UInt64): _description_
            max_payments (arc4.UInt64): _description_

        Returns:
            UInt64: _description_
        """
        assert Txn.sender == Global.creator_address, "Only the contract creator can call this method"
        return (
            itxn.AssetConfig(
                asset_name=Global.creator_address.bytes,
                unit_name=arc4.UInt64(Global.current_application_address.total_assets_created).bytes,
                total=max_payments.native,
                decimals=0,
                metadata_hash=active_from.bytes
                + payment_amount.bytes
                + payment_frequency.bytes
                + arc4.UInt64(Global.round).bytes,
                manager=Global.current_application_address,
                reserve=initial_redeemer,
                freeze=Global.current_application_address,
                clawback=Global.current_application_address,
                fee=0,
            )
            .submit()
            .created_asset.id
        )

    @arc4.abimethod
    def withdraw_tokens(self, subscription: Asset) -> None:
        """Transfers the subscription tokens to the initial redeemer.

        Args:
            subscription (Asset): The subscription token.
        """
        assert subscription.reserve == Txn.sender
        itxn.AssetTransfer(
            xfer_asset=subscription, asset_receiver=Txn.sender, asset_amount=subscription.total, fee=0
        ).submit()

    @arc4.abimethod
    def active_from(self, subscription: Asset) -> UInt64:
        """Parses the 'active from' round number from the subscription token.

        Args:
            subscription (Asset): The subscription token.

        Returns:
            UInt64: The 'active from' round number.
        """
        return op.extract_uint64(subscription.metadata_hash, 0)

    @arc4.abimethod
    def payment_amount(self, subscription: Asset) -> UInt64:
        """Parses the payment amount from the subscription token.

        Args:
            subscription (Asset): The subscription token.

        Returns:
            UInt64: The payment amount in MicroAlgos.
        """
        return op.extract_uint64(subscription.metadata_hash, 8)

    @arc4.abimethod
    def payment_frequency(self, subscription: Asset) -> UInt64:
        """Parses the payment frequency from the subscription token.

        Args:
            subscription (Asset): The subscription token.

        Returns:
            UInt64: The payment frequency (number of rounds).
        """
        return op.extract_uint64(subscription.metadata_hash, 16)

    @arc4.abimethod
    def cycle_number(self, subscription: Asset, at_round: UInt64) -> UInt64:
        """Calculates the payment cycle number 'as at' a specific round.

        Args:
            subscription (Asset): The subscription token.
            at_round (UInt64): The round to calculate the payment cycle 'as at'.

        Returns:
            UInt64: The payment cycle number.
        """
        active_from = self.active_from(subscription)
        return (
            UInt64(0)
            if at_round < active_from
            else (at_round - active_from) // self.payment_frequency(subscription) + 1
        )

    @arc4.abimethod
    def claim_payment(self, axfer: gtxn.AssetTransferTransaction) -> UInt64:
        """Makes a payment to the subscription token owner, if eligible.

        Args:
            axfer (gtxn.AssetTransferTransaction): The transaction transferring a unit of the subscription token to the contract account.

        Returns:
            UInt64: The amount of MicroAlgos paid.
        """
        subscription = axfer.xfer_asset
        assert (
            subscription.creator == Global.current_application_address
        ), "Asset must have been created by this application"
        assert axfer.asset_receiver == Global.current_application_address, "Asset receiver must be application account"
        assert axfer.asset_amount == 1, "Asset amount must be 1"

        cycle_number = self.cycle_number(subscription, Global.round)
        next_balance = subscription.balance(Global.current_application_address) + 1
        assert not next_balance > cycle_number, "Cannot claim payment for future cycle"
        if next_balance == cycle_number:
            return (
                itxn.Payment(
                    receiver=axfer.sender,
                    amount=self.payment_amount(subscription),
                    fee=0,
                )
                .submit()
                .amount
            )
        return UInt64(0)
