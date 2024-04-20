import algokit_utils
import pytest
from algokit_utils import (
    Account,
    TransactionParameters,
    TransferParameters,
    transfer,
)
from algokit_utils.config import config
from algosdk.atomic_transaction_composer import (
    AccountTransactionSigner,
    TransactionWithSigner,
)
from algosdk.transaction import PaymentTxn
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient

from smart_contracts.artifacts.utxo.client import UtxoClient


@pytest.fixture(scope="session")
def app_client(account: Account, algod_client: AlgodClient, indexer_client: IndexerClient) -> UtxoClient:
    config.configure(
        debug=True,
        # trace_all=True,
    )

    client = UtxoClient(
        algod_client,
        creator=account,
        indexer_client=indexer_client,
    )

    client.deploy(
        on_schema_break=algokit_utils.OnSchemaBreak.AppendApp,
        on_update=algokit_utils.OnUpdate.AppendApp,
    )

    transfer(
        algod_client,
        TransferParameters(
            from_account=account,
            to_address=client.app_address,
            micro_algos=1_000_000,
        ),
    )

    return client


def test_convert_algo_to_utxo(account: Account, app_client: UtxoClient) -> None:
    """Tests the convert_algo_to_utxo() method."""

    sp = app_client.algod_client.suggested_params()
    sp.fee = 2_000
    sp.flat_fee = True

    ptxn = PaymentTxn(
        sender=account.address,
        sp=sp,
        receiver=app_client.app_address,
        amt=7_000,
    )
    signer = AccountTransactionSigner(account.private_key)
    asset_id = app_client.convert_algo_to_utxo(payment=TransactionWithSigner(ptxn, signer)).return_value
    utxo_value = app_client.value(utxo=asset_id).return_value

    assert isinstance(asset_id, int) and asset_id > 0, "Asset creation failed"
    assert utxo_value == 7_000, "Incorrect UTXO value"


def test_process_transaction(account: Account, app_client: UtxoClient) -> None:
    """Tests the process_transaction() method."""

    sp = app_client.algod_client.suggested_params()
    sp.fee = 2_000
    sp.flat_fee = True

    def create_utxo(amount: int) -> int:
        ptxn = PaymentTxn(
            sender=account.address,
            sp=sp,
            receiver=app_client.app_address,
            amt=amount,
        )
        signer = AccountTransactionSigner(account.private_key)
        return app_client.convert_algo_to_utxo(
            payment=TransactionWithSigner(ptxn, signer),
            transaction_parameters=TransactionParameters(suggested_params=sp),
        ).return_value

    asset_1 = create_utxo(10_000)
    asset_2 = create_utxo(20_000)

    sp = app_client.algod_client.suggested_params()
    sp.fee = 5_000
    sp.flat_fee = True

    app_client.process_transaction(
        tx_ins=[asset_1, asset_2],
        tx_outs=[(account.address, 25_000), (account.address, 5_000)],
        transaction_parameters=TransactionParameters(suggested_params=sp, foreign_assets=[asset_1, asset_2]),
    )


def test_convert_utxo_to_algo(account: Account, app_client: UtxoClient) -> None:
    """Tests the convert_utxo_to_algo() method."""
    sp = app_client.algod_client.suggested_params()
    sp.fee = 3_000
    sp.flat_fee = True

    ptxn = PaymentTxn(
        sender=account.address,
        sp=sp,
        receiver=app_client.app_address,
        amt=100_000,
    )
    signer = AccountTransactionSigner(account.private_key)
    asset_id = app_client.convert_algo_to_utxo(payment=TransactionWithSigner(ptxn, signer)).return_value

    balance_before = app_client.algod_client.account_info(account.address)["amount"]

    app_client.convert_utxo_to_algo(utxo=asset_id, transaction_parameters=TransactionParameters(suggested_params=sp))

    balance_after = app_client.algod_client.account_info(account.address)["amount"]

    assert balance_after == balance_before + 100_000 - 3_000, "Incorrect balance after converting back to Algos"
