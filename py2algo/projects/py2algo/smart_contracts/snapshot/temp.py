import base64
import sys
from pathlib import Path

import algokit_utils
from algokit_utils import (
    TransactionParameters,
    TransferParameters,
    get_algod_client,
    get_indexer_client,
    get_localnet_default_account,
    transfer,
)
from algosdk import abi
from algosdk.transaction import SuggestedParams
from algosdk.v2client.algod import AlgodClient
from dotenv import load_dotenv

base_path = Path(__file__).parent.parent.parent

sys.path.append(base_path.as_posix())

from smart_contracts.artifacts.snapshot.client import SnapshotClient

load_dotenv(base_path / ".env.localnet")

algod_client = get_algod_client()
indexer_client = get_indexer_client()
account = get_localnet_default_account(algod_client)


def flat_fee(algod_client: AlgodClient, fee: int) -> SuggestedParams:
    sp = algod_client.suggested_params()
    sp.fee = fee
    sp.flat_fee = True
    return sp


client = SnapshotClient(
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

print(f"{account.address=}")
print(f"{client.app_id=}")

snapshot_id = client.mint_snapshot(
    account=account.address,
    asset=0,
    transaction_parameters=TransactionParameters(suggested_params=flat_fee(algod_client, 2_000)),
).return_value

print(f"{snapshot_id=}")

metadata = base64.b64decode(algod_client.asset_info(snapshot_id)["params"]["metadata-hash"])

at_round, at_timestamp, asset_id, balance = abi.ABIType.from_string("(uint64,uint64,uint64,uint64)").decode(metadata)

print(f"{at_round=}, {at_timestamp=}, {asset_id=}, {balance=}")
