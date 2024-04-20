# pyright: reportMissingModuleSource=false
from typing import TypeAlias

from algopy import Account, ARC4Contract, Asset, Bytes, Global, Txn, UInt64, arc4, gtxn, itxn, op, subroutine, urange


class TxOut(arc4.Struct, kw_only=True):
    lock: arc4.Address
    value: arc4.UInt64


Inputs: TypeAlias = arc4.DynamicArray[arc4.UInt64]
Outputs: TypeAlias = arc4.DynamicArray[TxOut]


class Utxo(ARC4Contract):
    """A contract that simulates UTXOs on Algorand."""

    @subroutine
    def _mint_utxo(self, lock: Account, value: Bytes) -> Asset:
        """An internal method that mints a UTXO.

        Args:
            lock (Account): The address that locks the UTXO.
            value (Bytes): The value of the UTXO.

        Returns:
            Asset: The UTXO asset.
        """
        return (
            itxn.AssetConfig(
                asset_name="UTXO",
                total=1,
                decimals=0,
                metadata_hash=value + op.bzero(24),
                reserve=lock,
                fee=0,
            )
            .submit()
            .created_asset
        )

    @subroutine
    def _burn_utxo(self, utxo: Asset) -> None:
        """An internal method that burns a UTXO.

        Args:
            utxo (Asset): The UTXO asset to burn.
        """
        itxn.AssetConfig(
            config_asset=utxo,
            sender=Global.current_application_address,
            fee=0,
        ).submit()

    @arc4.abimethod
    def convert_algo_to_utxo(self, payment: gtxn.PaymentTransaction) -> UInt64:
        """Converts Algos to a UTXO.

        Args:
            payment (gtxn.PaymentTransaction): The payment transaction.

        Returns:
            UInt64: The ID of the UTXO asset created.
        """
        assert (
            payment.receiver == Global.current_application_address
        ), "Payment receiver must be the application address"

        return self._mint_utxo(lock=Txn.sender, value=op.itob(payment.amount)).id

    @arc4.abimethod
    def convert_utxo_to_algo(self, utxo: Asset) -> None:
        """Converts a UTXO to Algos.

        Args:
            utxo (Asset): The UTXO asset to convert.
        """
        assert utxo.reserve == Txn.sender, "UTXO must be locked by the sender"
        itxn.Payment(
            receiver=Txn.sender,
            amount=self.value(utxo),
            fee=0,
        ).submit()
        self._burn_utxo(utxo)

    @arc4.abimethod
    def value(self, utxo: Asset) -> UInt64:
        """Parses the value of a UTXO from its metadata hash.

        Args:
            utxo (Asset): The UTXO asset.

        Returns:
            UInt64: The value of the UTXO.
        """
        return op.extract_uint64(utxo.metadata_hash, 0)

    @arc4.abimethod
    def process_transaction(self, tx_ins: Inputs, tx_outs: Outputs) -> None:
        """Validates and processes a UTXO transaction.

        Args:
            tx_ins (Inputs): Array of UTXO asset IDs to spend.
            tx_outs (Outputs): Array of (address, value) tuples to create UTXOs for.
        """
        assert tx_ins, "Must provide at least one input"
        assert tx_outs, "Must provide at least one output"

        tx_in_total = UInt64(0)
        for tx_in in tx_ins:
            utxo = Asset(tx_in.native)
            assert utxo.creator == Global.current_application_address, "Input must be created by the application"
            assert utxo.reserve == Txn.sender, "Input must be locked by the sender"
            tx_in_value = self.value(utxo)
            self._burn_utxo(utxo)
            tx_in_total += tx_in_value

        tx_out_total = UInt64(0)
        for i in urange(tx_outs.length):
            tx_out = tx_outs[i].copy()
            self._mint_utxo(lock=Account(tx_out.lock.bytes), value=tx_out.value.bytes)
            tx_out_total += tx_out.value.native

        assert tx_in_total == tx_out_total, "Total input value must equal total output value"
