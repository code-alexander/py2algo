from base64 import b64decode

import algokit_utils
import pytest
from algokit_utils import TransactionParameters, TransferParameters, get_localnet_default_account, opt_in, transfer
from algokit_utils.config import config
from algosdk.atomic_transaction_composer import (
    AccountTransactionSigner,
    TransactionWithSigner,
)
from algosdk.transaction import AssetTransferTxn
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient
from pydantic import BaseModel
from sympy import Piecewise, symbols

from smart_contracts.artifacts.tokenised_subscriptions.client import TokenisedSubscriptionsClient


@pytest.fixture(scope="session")
def app_client(algod_client: AlgodClient, indexer_client: IndexerClient) -> TokenisedSubscriptionsClient:
    account = get_localnet_default_account(algod_client)

    config.configure(
        debug=True,
        # trace_all=True,
    )

    client = TokenisedSubscriptionsClient(
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
            micro_algos=1_000_000_000,
        ),
    )

    return client


class Subscription(BaseModel):
    asset_id: int
    initial_redeemer: str
    active_from: int
    payment_amount: int
    payment_frequency: int
    max_payments: int


@pytest.fixture
def subscription(algod_client: AlgodClient, app_client: TokenisedSubscriptionsClient) -> Subscription:
    last_round = algod_client.status()["last-round"]
    account = get_localnet_default_account(algod_client)

    sp = app_client.algod_client.suggested_params()
    sp.fee = 2_000
    sp.flat_fee = True

    initial_redeemer = account.address
    active_from = last_round
    payment_amount = 1_000_000
    payment_frequency = 5
    max_payments = 10

    asset_id = app_client.mint_tokens(
        initial_redeemer=initial_redeemer,
        active_from=active_from,
        payment_amount=payment_amount,
        payment_frequency=payment_frequency,
        max_payments=max_payments,
        transaction_parameters=TransactionParameters(suggested_params=sp),
    ).return_value

    return Subscription(
        asset_id=asset_id,
        initial_redeemer=initial_redeemer,
        active_from=active_from,
        payment_amount=payment_amount,
        payment_frequency=payment_frequency,
        max_payments=max_payments,
    )


def test_mint_tokens(
    algod_client: AlgodClient, app_client: TokenisedSubscriptionsClient, subscription: Subscription
) -> None:
    """Tests the mint_tokens() and withdraw_tokens() methods."""
    assert isinstance(subscription.asset_id, int) and subscription.asset_id > 0, "Asset minting failed"

    app_balance = algod_client.account_asset_info(address=app_client.app_address, asset_id=subscription.asset_id)[
        "asset-holding"
    ]["amount"]
    assert app_balance == subscription.max_payments, "Asset not owned by application account"


def test_asset_params(
    algod_client: AlgodClient, app_client: TokenisedSubscriptionsClient, subscription: Subscription
) -> None:
    """Tests the subscription token's asset params."""
    asset_params = algod_client.asset_info(subscription.asset_id)["params"]

    assert asset_params["total"] == subscription.max_payments, "Asset total units is incorrect"
    assert (
        asset_params["creator"]
        == asset_params["manager"]
        == asset_params["freeze"]
        == asset_params["clawback"]
        == app_client.app_address
    ), "Incorrect asset params"
    assert asset_params["reserve"] == subscription.initial_redeemer, "Incorrect initial redeemer"

    # Check token state in metadata hash
    datum = b64decode(asset_params["metadata-hash"])
    btoi = lambda b: int.from_bytes(b, "big")
    active_from = btoi(datum[0:8])
    payment_amount = btoi(datum[8:16])
    payment_frequency = btoi(datum[16:24])

    assert active_from == subscription.active_from, "Incorrect active from round"
    assert payment_amount == subscription.payment_amount, "Incorrect payment amount"
    assert payment_frequency == subscription.payment_frequency, "Incorrect payment_frequency"


def test_withdraw_tokens(
    algod_client: AlgodClient, app_client: TokenisedSubscriptionsClient, subscription: Subscription
) -> None:
    """Tests the withdraw_tokens() method."""
    account = get_localnet_default_account(algod_client)
    opt_in(algod_client, account, asset_ids=[subscription.asset_id])

    sp = app_client.algod_client.suggested_params()
    sp.fee = 2_000
    sp.flat_fee = True

    balance_before = algod_client.account_asset_info(account.address, subscription.asset_id)["asset-holding"]["amount"]
    assert balance_before == 0, "Starting balance of token should be zero"
    app_client.withdraw_tokens(
        subscription=subscription.asset_id, transaction_parameters=TransactionParameters(suggested_params=sp)
    )
    balance_after = algod_client.account_asset_info(account.address, subscription.asset_id)["asset-holding"]["amount"]
    assert balance_after == subscription.max_payments, "Balance of token after withdrawing is incorrect"


def test_cycle_number(app_client: TokenisedSubscriptionsClient, subscription: Subscription) -> None:
    """Tests the cycle_number() method against a reference implementation in Sympy."""
    active_from, payment_frequency, at_round = symbols(
        r"{active\_from} {payment\_frequency} {at\_round}", integer=True, nonnegative=True
    )
    # Sympy reference implementation
    expr = Piecewise(
        (0, at_round < active_from), ((at_round - active_from) // payment_frequency + 1, True), evaluate=False
    )

    for r in range(subscription.active_from - 2, subscription.active_from + subscription.max_payments + 10):
        reference_value = int(
            expr.subs(
                [
                    (active_from, subscription.active_from),
                    (at_round, r),
                    (payment_frequency, subscription.payment_frequency),
                ]
            )
        )
        assert (
            app_client.cycle_number(subscription=subscription.asset_id, at_round=r).return_value == reference_value
        ), "Cycle number does not match Sympy reference implementation"


def test_claim_payment(
    algod_client: AlgodClient, app_client: TokenisedSubscriptionsClient, subscription: Subscription
) -> None:
    """Tests the claim_payment() method."""

    account = get_localnet_default_account(algod_client)
    opt_in(algod_client, account, asset_ids=[subscription.asset_id])

    sp = app_client.algod_client.suggested_params()
    sp.fee = 2_000
    sp.flat_fee = True

    # Withdraw subscription tokens first
    app_client.withdraw_tokens(
        subscription=subscription.asset_id, transaction_parameters=TransactionParameters(suggested_params=sp)
    )

    account_balance_start = algod_client.account_info(account.address)["amount"]

    fees = 0
    received = 0

    while True:
        token_balance = algod_client.account_asset_info(account.address, subscription.asset_id)["asset-holding"][
            "amount"
        ]

        if not token_balance:
            break
        try:
            axfer_txn = AssetTransferTxn(
                sp=sp,
                sender=account.address,
                receiver=app_client.app_address,
                amt=1,
                index=subscription.asset_id,
            )
            received += app_client.claim_payment(
                axfer=TransactionWithSigner(txn=axfer_txn, signer=AccountTransactionSigner(account.private_key))
            ).return_value

            fees += 3_000
        except algokit_utils.logic_error.LogicError:
            # Trigger another round on test net
            app_client.cycle_number(subscription=subscription.asset_id, at_round=0)
            fees += 1_000

    account_balance_end = algod_client.account_info(account.address)["amount"]
    token_balance_end = algod_client.account_asset_info(account.address, subscription.asset_id)["asset-holding"][
        "amount"
    ]
    assert token_balance_end == 0, "Tokens not transferred"
    assert (
        account_balance_end == account_balance_start + (subscription.max_payments * subscription.payment_amount) - fees
    ), "Incorrect balances after withdrawing"
    assert received == subscription.max_payments * subscription.payment_amount, "Incorrect amount received"
