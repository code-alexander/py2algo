import sys
from pathlib import Path

import algokit_utils
from algokit_utils import (
    TransferParameters,
    get_algod_client,
    get_indexer_client,
    get_localnet_default_account,
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
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).parent.parent.parent.parent) + "/")

from smart_contracts.artifacts.utxo.client import UtxoClient

env_path = Path(__file__).parent.parent.parent.parent / ".env.localnet"
load_dotenv(env_path)

algod_client = get_algod_client()
indexer_client = get_indexer_client()
account = get_localnet_default_account(algod_client)


def app_client(algod_client: AlgodClient, indexer_client: IndexerClient) -> UtxoClient:
    config.configure(
        debug=True,
        # trace_all=True,
    )

    client = UtxoClient(
        algod_client,
        creator=get_localnet_default_account(algod_client),
        indexer_client=indexer_client,
    )

    client.deploy(
        on_schema_break=algokit_utils.OnSchemaBreak.AppendApp,
        on_update=algokit_utils.OnUpdate.AppendApp,
    )

    transfer(
        algod_client,
        TransferParameters(
            from_account=get_localnet_default_account(algod_client),
            to_address=client.app_address,
            micro_algos=1_000_000,
        ),
    )

    return client


app = app_client(algod_client, indexer_client)
print(app)


sp = app.algod_client.suggested_params()
sp.fee = 2_000
sp.flat_fee = True

ptxn = PaymentTxn(
    sender=account.address,
    sp=sp,
    receiver=app.app_address,
    amt=7_000,
)

signer = AccountTransactionSigner(account.private_key)

asset_id = app.convert_algo_to_utxo(payment=TransactionWithSigner(ptxn, signer)).return_value

print(f"Asset ID: {asset_id}")

utxo_value = app.value(utxo=asset_id).return_value
print(f"UTXO Value: {utxo_value}")


# def test_question_one(app_client: UtxoClient) -> None:
#     """Tests the question_one() method."""
#     assert app_client.question_one().return_value == 20
