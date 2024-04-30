import base64
import time
from functools import reduce

import pytest
from algokit_utils import (
    Account,
    EnsureBalanceParameters,
    TransactionParameters,
    TransferParameters,
    ensure_funded,
    get_account,
    transfer,
)
from algokit_utils.config import config
from algosdk import encoding
from algosdk.atomic_transaction_composer import (
    AccountTransactionSigner,
    TransactionWithSigner,
)
from algosdk.transaction import PaymentTxn, SuggestedParams
from algosdk.util import algos_to_microalgos
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient

from smart_contracts.artifacts.venture_funding.venture_funding_client import VentureFundingClient


@pytest.fixture(scope="session")
def app_client(account: Account, algod_client: AlgodClient, indexer_client: IndexerClient) -> VentureFundingClient:
    config.configure(
        debug=True,
        # trace_all=True,
    )

    client = VentureFundingClient(
        algod_client,
        creator=account,
        indexer_client=indexer_client,
    )

    last_round = algod_client.status()["last-round"]

    client.create_new_project(
        project_name="Test Project",
        funding_target=algos_to_microalgos(1_000),
        funding_deadline=last_round + 6,
        minimum_pledge=algos_to_microalgos(10),
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


def flat_fee(algod_client: AlgodClient, fee: int) -> SuggestedParams:
    sp = algod_client.suggested_params()
    sp.fee = fee
    sp.flat_fee = True
    return sp


def test_new_project(app_client: VentureFundingClient) -> None:
    """Tests the new_project() method."""

    state = {k: getattr(v, "as_str", v) for k, v in app_client.get_global_state().__dict__.items()}

    assert state["project_name"] == "Test Project", "Incorrect project name"
    assert state["funding_target"] == algos_to_microalgos(1_000), "Incorrect funding target"
    assert isinstance(state["funding_deadline"], int) and state["funding_deadline"] > 0, "Invalid funding deadline"
    assert state["minimum_pledge"] == algos_to_microalgos(10), "Incorrect minimum pledge"
    assert isinstance(state["pledged_amount"], int) and state["pledged_amount"] == 0, "Incorrect initial pledged amount"


def test_pledge(account: Account, app_client: VentureFundingClient) -> None:
    """Tests the pledge() method."""

    txn = PaymentTxn(
        sender=account.address,
        receiver=app_client.app_address,
        amt=algos_to_microalgos(75),
        sp=app_client.algod_client.suggested_params(),
    )

    signer = AccountTransactionSigner(account.private_key)

    pledged_amount = app_client.pledge(
        payment=TransactionWithSigner(txn, signer),
        transaction_parameters=TransactionParameters(
            suggested_params=flat_fee(app_client.algod_client, 4_000),
            boxes=[(0, encoding.decode_address(account.address))],
        ),
    ).return_value

    assert pledged_amount == algos_to_microalgos(75), "Incorrect pledge amount value returned"
    assert app_client.get_global_state().pledged_amount == algos_to_microalgos(
        75
    ), "Incorrect pledged amount in global state"


def test_withdraw_funds(account: Account, app_client: VentureFundingClient, indexer_client: IndexerClient) -> None:
    """Tests the withdraw_funds() method."""

    target_delta = app_client.get_global_state().funding_target - app_client.get_global_state().pledged_amount

    # Generate new account to simulate a second backer
    backer_b = get_account(app_client.algod_client, "backer_b")

    parameters = EnsureBalanceParameters(
        account_to_fund=backer_b,
        min_spending_balance_micro_algos=target_delta + 10_000,  # target delta + buffer for fees
    )

    ensure_funded(app_client.algod_client, parameters)

    txn = PaymentTxn(
        sender=backer_b.address,
        receiver=app_client.app_address,
        amt=target_delta,
        sp=app_client.algod_client.suggested_params(),
    )

    signer = AccountTransactionSigner(backer_b.private_key)

    backer_b_bytes = encoding.decode_address(backer_b.address)

    # Fund the remaining amount to meet the target
    app_client.pledge(
        payment=TransactionWithSigner(txn, signer),
        transaction_parameters=TransactionParameters(
            suggested_params=flat_fee(app_client.algod_client, 4_000), boxes=[(0, backer_b_bytes)]
        ),
    ).return_value

    assert (
        app_client.get_global_state().funding_target - app_client.get_global_state().pledged_amount == 0
    ), "Funding target not met"

    backers = [
        base64.b64decode(x["name"]) for x in app_client.algod_client.application_boxes(app_client.app_id)["boxes"]
    ]

    time.sleep(5)  # Wait for indexer to catch up

    backer_vault_map = {
        backer: base64.b64decode(indexer_client.application_box_by_name(app_client.app_id, backer)["value"])
        for backer in backers
    }

    get_balance = lambda a: app_client.algod_client.account_info(a)["amount"]

    total_vault_balance = reduce(
        lambda balance, vault: balance + get_balance(encoding.encode_address(vault)), backer_vault_map.values(), 0
    )

    withdrawn_amount = 0

    creator_balance_start = get_balance(account.address)

    for backer, vault in backer_vault_map.items():
        withdrawn_amount += app_client.withdraw_funds_from(
            backer=backer,
            transaction_parameters=TransactionParameters(
                accounts=[encoding.encode_address(backer), encoding.encode_address(vault)],
                boxes=[(0, backer)],
                suggested_params=flat_fee(app_client.algod_client, 4_000),
            ),
        ).return_value[0]  # the invested amount

    assert withdrawn_amount == total_vault_balance, "Incorrect withdrawn amount values returned"
    assert (
        creator_balance_start + withdrawn_amount >= get_balance(account.address) - 10_000
    ), "Incorrect creator balance after withdrawing funds"
