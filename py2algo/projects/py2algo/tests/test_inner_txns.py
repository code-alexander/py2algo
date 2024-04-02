import algokit_utils
import pytest
from algokit_utils import (
    TransactionParameters,
    TransferAssetParameters,
    TransferParameters,
    get_localnet_default_account,
    transfer,
    transfer_asset,
)
from algokit_utils.config import config
from algosdk import transaction
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient

from smart_contracts.artifacts.inner_txns.client import InnerClient


@pytest.fixture(scope="session")
def app_client(algod_client: AlgodClient, indexer_client: IndexerClient) -> InnerClient:
    account = get_localnet_default_account(algod_client)

    config.configure(
        debug=True,
        # trace_all=True,
    )

    client = InnerClient(
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
            from_account=get_localnet_default_account(algod_client),
            to_address=client.app_address,
            micro_algos=100_000,
        ),
    )

    return client


def test_mint_nft(app_client: InnerClient) -> None:
    """Tests the mint_nft() method."""
    sp = app_client.algod_client.suggested_params()
    sp.fee = 2_000
    sp.flat_fee = True
    transfer(
        app_client.algod_client,
        TransferParameters(
            from_account=get_localnet_default_account(app_client.algod_client),
            to_address=app_client.app_address,
            micro_algos=100_000,
        ),
    )

    asset_id = app_client.mint_nft(transaction_parameters=TransactionParameters(suggested_params=sp)).return_value
    assert isinstance(asset_id, int)

    asset_params = app_client.algod_client.asset_info(asset_id)["params"]
    assert asset_params["creator"] == app_client.app_address
    assert asset_params["total"] == 1
    assert asset_params["decimals"] == 0
    assert asset_params["name"] == "DOG"
    assert asset_params["unit-name"] == f"DOG_{app_client.get_global_state().counter}"


def test_opt_in(app_client: InnerClient) -> None:
    """Tests the opt_in() method."""
    algod_client = app_client.algod_client
    account = get_localnet_default_account(algod_client)
    txn = transaction.AssetConfigTxn(
        sender=account.address,
        sp=algod_client.suggested_params(),
        default_frozen=False,
        unit_name="rug",
        asset_name="Really Useful Gift",
        manager=account.address,
        reserve=account.address,
        freeze=account.address,
        clawback=account.address,
        url="https://path/to/my/asset/details",
        total=1000,
        decimals=0,
    )
    stxn = txn.sign(account.private_key)
    txid = algod_client.send_transaction(stxn)
    results = transaction.wait_for_confirmation(algod_client, txid, 4)
    created_asset = results["asset-index"]

    sp = algod_client.suggested_params()
    sp.fee = 2_000
    sp.flat_fee = True

    transfer(
        algod_client,
        TransferParameters(
            from_account=account,
            to_address=app_client.app_address,
            micro_algos=100_000,
        ),
    )

    app_client.opt_in(asset=created_asset, transaction_parameters=TransactionParameters(suggested_params=sp))

    transfer_asset(
        algod_client,
        TransferAssetParameters(
            from_account=account,
            to_address=app_client.app_address,
            asset_id=created_asset,
            amount=1,
        ),
    )

    asset_holding = algod_client.account_asset_info(address=app_client.app_address, asset_id=created_asset)[
        "asset-holding"
    ]

    assert asset_holding["asset-id"] == created_asset
    assert asset_holding["amount"] == 1


def test_withdraw(app_client: InnerClient) -> None:
    """Tests the withdraw() method."""
    algod_client = app_client.algod_client
    account = get_localnet_default_account(algod_client)
    transfer(
        algod_client,
        TransferParameters(
            from_account=account,
            to_address=app_client.app_address,
            micro_algos=2_000_000,
        ),
    )
    balance = lambda a: algod_client.account_info(a.address)["amount"]
    balance_before = balance(account)

    sp = algod_client.suggested_params()
    sp.fee = 2_000
    sp.flat_fee = True
    app_client.withdraw(amount=500_000, transaction_parameters=TransactionParameters(suggested_params=sp))
    assert balance(account) - balance_before == 500_000 - 2_000
