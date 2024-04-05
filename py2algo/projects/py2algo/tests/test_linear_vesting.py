import pytest
from algokit_utils import (
    TransactionParameters,
    TransferParameters,
    get_localnet_default_account,
    transfer,
)
from algokit_utils.config import config
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient
from sympy import Piecewise, symbols

from smart_contracts.artifacts.linear_vesting.client import VestingClient


@pytest.fixture(scope="session")
def app_client(algod_client: AlgodClient, indexer_client: IndexerClient) -> VestingClient:
    account = get_localnet_default_account(algod_client)

    config.configure(
        debug=True,
        # trace_all=True,
    )

    client = VestingClient(
        algod_client,
        creator=account,
        indexer_client=indexer_client,
    )

    last_round = algod_client.status()["last-round"]

    client.create_new(
        beneficiary=account.address,
        start=last_round + 10,
        duration=100,
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


def vesting_reference(p_allocation: int, p_start: int, p_duration: int, p_round: int) -> int:
    """Linear vesting reference implementation in sympy to test against.

    Args:
        p_allocation (int): The allocation amount to substitute in the expression.
        p_start (int): The start round to substitute in the expression.
        p_duration (int): The duration rounds to substitute in the expression.
        p_round (int): The round number to substitute in the expression.

    Returns:
        int: The integer vesting amount.
    """
    allocation, at, start, duration = symbols("allocation round start duration", integer=True, positive=True)
    expr = Piecewise(
        (0, at < start),
        (allocation, at >= start + duration),
        ((allocation * (at - start)) // duration, True),  # True = otherwise
    )
    return int(expr.subs([(allocation, p_allocation), (start, p_start), (duration, p_duration), (at, p_round)]))


@pytest.mark.parametrize(
    "p_allocation, p_start, p_duration", [(100, 0, 100), (1_000_000_000, 50_000, 1_000_000), (12, 0, 100)]
)
def test_calculate_vesting(app_client: VestingClient, p_allocation: int, p_start: int, p_duration: int) -> None:
    """Tests the calculate_vesting() method against a reference implementation in sympy."""

    for r in range(max(p_start - 1, 0), p_duration + 1, min(p_duration, 10_000)):
        ref_amount = vesting_reference(p_allocation, p_start, p_duration, r)

        amount = app_client.calculate_vesting(
            allocation=p_allocation, start=p_start, duration=p_duration, at=r
        ).return_value

        assert ref_amount == amount, "Vesting amount does not match sympy reference calculation"


def test_release_funds(app_client: VestingClient) -> None:
    """Tests the release_funds() method."""

    algod_client = app_client.algod_client
    account = get_localnet_default_account(algod_client)
    balance = lambda a: algod_client.account_info(a)["amount"]
    balance_before = balance(account.address)
    app_balance_before = balance(app_client.app_address)

    state = app_client.get_global_state()
    allocation = app_balance_before + state.released
    start = state.start
    duration = state.duration

    sp = algod_client.suggested_params()
    sp.fee = 2_000
    sp.flat_fee = True
    r = app_client.release_funds(transaction_parameters=TransactionParameters(suggested_params=sp)).confirmed_round

    ref_amount = vesting_reference(allocation, start, duration, r)

    assert balance(account.address) == balance_before + ref_amount - state.released - 2_000
