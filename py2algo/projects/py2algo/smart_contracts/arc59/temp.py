import sys
from pathlib import Path

import algokit_utils
from algokit_utils import (
    Account,
    TransactionParameters,
    TransferAssetParameters,
    TransferParameters,
    get_algod_client,
    get_indexer_client,
    get_localnet_default_account,
    transfer,
    transfer_asset,
)
from algosdk.transaction import AssetCreateTxn, SuggestedParams, wait_for_confirmation
from algosdk.util import algos_to_microalgos
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient
from dotenv import load_dotenv

base_path = Path(__file__).parent.parent.parent

sys.path.append(base_path.as_posix())

from smart_contracts.artifacts.arc59.arc59_client import Arc59Client

load_dotenv(base_path / ".env.localnet")

algod_client = get_algod_client()
indexer_client = get_indexer_client()
account = get_localnet_default_account(algod_client)


def deploy_arc59_app(algod_client: AlgodClient, indexer_client: IndexerClient):
    client = Arc59Client(
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
            micro_algos=algos_to_microalgos(7_500),
        ),
    )
    return client


arc59_app = deploy_arc59_app(algod_client, indexer_client)
print(f"{arc59_app.app_id=}")


def mint_nft(algod_client: AlgodClient, account: Account) -> int:
    """Helper function to mint an NFT.

    Args:
        algod_client (AlgodClient): The Algod client.
        account (Account): The account to sign the transaction with.

    Returns:
        int: The asset ID of the NFT minted.
    """
    txn = AssetCreateTxn(
        sender=account.address,
        sp=algod_client.suggested_params(),
        total=1,
        decimals=0,
        default_frozen=False,
        unit_name="NFT",
        asset_name="NFT",
    )
    signed_txn = txn.sign(account.private_key)
    txid = algod_client.send_transaction(signed_txn)
    txn_result = wait_for_confirmation(algod_client, txid, 4)
    asset_id = txn_result["asset-index"]
    return asset_id


def flat_fee(algod_client: AlgodClient, fee: int) -> SuggestedParams:
    sp = algod_client.suggested_params()
    sp.fee = fee
    sp.flat_fee = True
    return sp


asset_id = mint_nft(algod_client, account)
print(f"{asset_id=}")

arc59_app.arc59_opt_router_in(
    asa=asset_id,
    transaction_parameters=TransactionParameters(
        suggested_params=flat_fee(algod_client, 2_000), foreign_assets=[asset_id]
    ),
)
axfer = transfer_asset(
    algod_client,
    TransferAssetParameters(from_account=account, to_address=arc59_app.app_address, asset_id=asset_id, amount=1),
)
print(axfer)
