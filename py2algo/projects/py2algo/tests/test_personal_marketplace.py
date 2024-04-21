import base64
import hashlib
import time
from datetime import datetime

import algokit_utils
import pytest
from algokit_utils import (
    Account,
    EnsureBalanceParameters,
    TransactionParameters,
    TransferParameters,
    ensure_funded,
    get_account,
    get_indexer_client,
    opt_in,
    transfer,
)
from algokit_utils.config import config
from algosdk import abi
from algosdk.atomic_transaction_composer import (
    AccountTransactionSigner,
    TransactionWithSigner,
)
from algosdk.transaction import AssetCreateTxn, AssetTransferTxn, PaymentTxn, wait_for_confirmation
from algosdk.util import algos_to_microalgos
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient
from pydantic import BaseModel

from smart_contracts.artifacts.personal_marketplace.client import PersonalMarketplaceClient


class SaleEvent(BaseModel):
    asset_id: int
    listed_price: int
    amount_paid: int
    buyer: str
    processed_round: int
    processed_timestamp: datetime


@pytest.fixture(scope="session")
def app_client(account: Account, algod_client: AlgodClient, indexer_client: IndexerClient) -> PersonalMarketplaceClient:
    config.configure(
        debug=True,
        # trace_all=True,
    )

    client = PersonalMarketplaceClient(
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


def _list_nft(account: Account, app_client: PersonalMarketplaceClient) -> None:
    """Helper function to list an NFT on the marketplace."""

    sp = app_client.algod_client.suggested_params()
    sp.fee = 2_000
    sp.flat_fee = True

    txn = AssetCreateTxn(
        sender=account.address,
        sp=sp,
        total=1,
        decimals=0,
        default_frozen=False,
        unit_name="NFT",
        asset_name="NFT",
    )
    signed_txn = txn.sign(account.private_key)
    txid = app_client.algod_client.send_transaction(signed_txn)
    txn_result = wait_for_confirmation(app_client.algod_client, txid, 4)
    asset_id = txn_result["asset-index"]

    app_client.opt_in(nft=asset_id, transaction_parameters=TransactionParameters(suggested_params=sp))

    axfer = AssetTransferTxn(
        sender=account.address,
        sp=sp,
        receiver=app_client.app_address,
        amt=1,
        index=asset_id,
    )

    app_client.list_nft(
        axfer=TransactionWithSigner(axfer, AccountTransactionSigner(account.private_key)),
        price=algos_to_microalgos(7_500),
        transaction_parameters=TransactionParameters(suggested_params=sp, boxes=[(0, asset_id)]),
    )

    return asset_id


def _is_sale_event(log: str):
    """Helper function to check if a log is a sale event."""
    sale_event_signature = "SaleEvent(uint64,uint64,uint64,address,uint64,uint64)"
    prefix = hashlib.new("sha512_256", sale_event_signature.encode()).digest()[:4]
    return base64.b64decode(log)[:4] == prefix


def test_list_nft(account: Account, app_client: PersonalMarketplaceClient) -> None:
    """Tests the convert_algo_to_utxo() method."""

    asset_id = _list_nft(account, app_client)

    # Check app account balance of NFT
    assert (
        app_client.algod_client.account_asset_info(app_client.app_address, asset_id)["asset-holding"]["amount"] == 1
    ), "NFT not transferred to app address"

    # Check box value (price) via Algod
    assert int.from_bytes(
        base64.b64decode(
            app_client.algod_client.application_box_by_name(app_client.app_id, int.to_bytes(asset_id, length=8))[
                "value"
            ]
        )
    ) == algos_to_microalgos(7_500), "NFT not listed"

    # Check box value (price) via app call
    assert app_client.price(
        nft=asset_id,
        transaction_parameters=TransactionParameters(boxes=[(0, asset_id)]),
    ).return_value == algos_to_microalgos(7_500), "Incorrect price returned from price() method"


def test_purchase_nft(account: Account, app_client: PersonalMarketplaceClient) -> None:
    """Tests the purchase_nft() method."""

    asset_id = _list_nft(account, app_client)

    # Generate new account to simulate buyer
    buyer = get_account(app_client.algod_client, "buyer")
    # Opt buyer in to receiver asset
    opt_in(app_client.algod_client, buyer, asset_ids=[asset_id])

    creator = app_client.creator().return_value
    assert creator == account.address, "Incorrect creator account"

    sale_price = app_client.price(
        nft=asset_id, transaction_parameters=TransactionParameters(boxes=[(0, asset_id)])
    ).return_value

    ptxn = PaymentTxn(
        sender=buyer.address,
        sp=app_client.algod_client.suggested_params(),
        receiver=account.address,
        amt=sale_price,
    )

    parameters = EnsureBalanceParameters(
        account_to_fund=buyer,
        min_spending_balance_micro_algos=sale_price + 100_000 + 2_000,  # price + MBR for new asset + fee
    )

    ensure_funded(app_client.algod_client, parameters)

    sp = app_client.algod_client.suggested_params()
    sp.fee = 2_000
    sp.flat_fee = True

    response = app_client.purchase_nft(
        nft=asset_id,
        payment=TransactionWithSigner(ptxn, AccountTransactionSigner(buyer.private_key)),
        transaction_parameters=TransactionParameters(
            suggested_params=sp, boxes=[(0, asset_id)], foreign_assets=[asset_id], accounts=[buyer.address]
        ),
    )

    assert (
        app_client.algod_client.account_asset_info(buyer.address, asset_id)["asset-holding"]["amount"] == 1
    ), "NFT not transferred to buyer"

    indexer_client = get_indexer_client()

    time.sleep(5)  # Wait for indexer to catch up
    logs = [
        item["logs"][0]
        for item in indexer_client.application_logs(app_client.app_id, min_round=response.confirmed_round)["log-data"]
        if item["logs"]
    ]

    sale_events = [log for log in logs if _is_sale_event(log)]
    assert sale_events, "No sale events found in application logs"

    last_sale_event = sale_events[-1]
    codec = abi.TupleType.from_string("(uint64,uint64,uint64,address,uint64,uint64)")
    decoded = codec.decode(base64.b64decode(last_sale_event)[4:])
    event = SaleEvent(**dict(zip(SaleEvent.__annotations__.keys(), decoded)))

    assert event.asset_id == asset_id, "Incorrect asset ID in sale event"
    assert event.listed_price == algos_to_microalgos(7_500), "Incorrect listed price in sale event"
    assert event.amount_paid == sale_price, "Incorrect amount paid in sale event"
    assert event.buyer == buyer.address, "Incorrect buyer in sale event"
    assert event.processed_round == response.confirmed_round, "Incorrect processed round in sale event"
