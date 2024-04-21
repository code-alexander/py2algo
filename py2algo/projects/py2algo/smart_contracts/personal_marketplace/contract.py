# pyright: reportMissingModuleSource=false


from algopy import (
    ARC4Contract,
    Asset,
    Bytes,
    Global,
    Txn,
    UInt64,
    arc4,
    gtxn,
    itxn,
    op,
    subroutine,
)


class SaleEvent(arc4.Struct):
    asset_id: arc4.UInt64
    listed_price: arc4.UInt64
    amount_paid: arc4.UInt64
    buyer: arc4.Address
    processed_round: arc4.UInt64
    processed_timestamp: arc4.UInt64


class PersonalMarketplace(ARC4Contract):
    """A simple contract for selling NFTs."""

    @arc4.abimethod
    def creator(self) -> arc4.Address:
        """A public method that returns the creator's address encoded as an ARC-4 ABI type.

        Returns:
            arc4.Address: The creator's address.
        """
        return arc4.Address(Global.creator_address)

    @subroutine
    def creator_only(self) -> None:
        """Causes the application call to fail if the transaction sender is not the creator."""
        assert Txn.sender == Global.creator_address, "Only the creator can call this method"

    @arc4.abimethod
    def opt_in(self, nft: Asset) -> None:
        """Opts the contract into an asset.

        Args:
            nft (Asset): The asset to opt in to.
        """
        self.creator_only()
        itxn.AssetTransfer(
            xfer_asset=nft,
            asset_receiver=Global.current_application_address,
            asset_amount=0,
            fee=0,
        ).submit()

    @subroutine
    def box_key(self, nft: Asset) -> Bytes:
        """Returns the box storage key for an NFT.

        Args:
            nft (Asset): The NFT.

        Returns:
            Bytes: The key for the NFT.
        """
        return op.itob(nft.id)

    @arc4.abimethod
    def list_nft(self, axfer: gtxn.AssetTransferTransaction, price: arc4.UInt64) -> None:
        """Lists an NFT for sale.

        Args:
            axfer (gtxn.AssetTransferTransaction): The transaction transferring the asset for sale to the contract.
            price (arc4.UInt64): The minimum price the asset can be sold for.
        """
        self.creator_only()
        assert (
            axfer.asset_receiver == Global.current_application_address
        ), "Asset receiver must be the application address"
        assert axfer.asset_amount == 1, "Asset amount must be 1"

        # Store sale price in box storage
        op.Box.put(self.box_key(axfer.xfer_asset), price.bytes)

    @arc4.abimethod
    def price(self, nft: Asset) -> UInt64:
        """Returns the minimum sale price for an NFT.

        Args:
            nft (Asset): The NFT.

        Returns:
            UInt64: The minimum sale price in MicroAlgos.
        """
        value, exists = op.Box.get(self.box_key(nft))
        assert exists, "Price not found"
        return op.btoi(value)

    @arc4.abimethod
    def purchase_nft(self, nft: Asset, payment: gtxn.PaymentTransaction) -> None:
        """Allows a user to purchase an NFT.

        Args:
            nft (Asset): The NFT being purchased.
            payment (gtxn.PaymentTransaction): The payment to the creator.
        """
        assert nft.balance(Global.current_application_address), "NFT not available for purchase"
        assert payment.sender.is_opted_in(nft), "Sender must opt in to receive NFT"
        assert payment.receiver == Global.creator_address, "Payment receiver must be the creator"
        assert payment.amount >= (listed_price := self.price(nft)), "Payment amount must be >= NFT price"

        itxn.AssetTransfer(
            xfer_asset=nft,
            asset_receiver=payment.sender,
            asset_amount=1,
            fee=0,
        ).submit()

        # Log sale event
        arc4.emit(
            SaleEvent(
                arc4.UInt64(nft.id),  # asset_id
                arc4.UInt64(listed_price),  # listed_price
                arc4.UInt64(payment.amount),  # amount_paid
                arc4.Address(payment.sender),  # buyer
                arc4.UInt64(Global.round),  # processed_round
                arc4.UInt64(Global.latest_timestamp),  # processed_timestamp
            )
        )

        # Remove listing
        _deleted = op.Box.delete(self.box_key(nft))
