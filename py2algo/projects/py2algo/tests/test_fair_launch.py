import pytest
from algokit_utils import (
    TransferParameters,
    get_localnet_default_account,
    transfer,
)
from algokit_utils.config import config
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient
from sympy import Piecewise, symbols

from smart_contracts.artifacts.fair_launch.client import FairLaunchClient


@pytest.fixture(scope="session")
def app_client(algod_client: AlgodClient, indexer_client: IndexerClient) -> FairLaunchClient:
    account = get_localnet_default_account(algod_client)

    config.configure(
        debug=True,
        # trace_all=True,
    )

    client = FairLaunchClient(
        algod_client,
        creator=account,
        indexer_client=indexer_client,
    )

    client.create_new(genesis_hash=b"test", zero_bits=10, difficulty_halving_interval=1, minimum_balance=1_000)

    transfer(
        algod_client,
        TransferParameters(
            from_account=get_localnet_default_account(algod_client),
            to_address=client.app_address,
            micro_algos=1_000_000_000,
        ),
    )

    return client


def target_reference(p_difficulty_halving_interval: int, p_zero_bits: int, p_at_round: int) -> int:
    """Target calculation reference implementation in sympy."""

    at_round, last_round, difficulty_halving_interval = symbols(
        r"{at\_round} {last\_round} {difficulty\_halving\_interval}", integer=True, nonnegative=True
    )

    halvings = (at_round - last_round) // difficulty_halving_interval

    zero_bits = symbols(r"{zero\_bits}", integer=True, nonnegative=True)

    TARGET_LIMIT = 2**64 - 1

    target_expr = Piecewise((TARGET_LIMIT, halvings > zero_bits), (TARGET_LIMIT // 2 ** (zero_bits - halvings), True))

    return int(
        target_expr.subs(
            [
                (difficulty_halving_interval, p_difficulty_halving_interval),
                (zero_bits, p_zero_bits),
                (last_round, 0),
                (at_round, p_at_round),
            ]
        )
    )


@pytest.mark.parametrize("p_difficulty_halving_interval, p_zero_bits, p_halvings", [(1, 8, 10), (1, 63, 70)])
def test_calculate_target(
    app_client: FairLaunchClient, p_difficulty_halving_interval: int, p_zero_bits: int, p_halvings: int
) -> None:
    """Tests the calculate_target() method against a reference implementation in sympy."""

    for r in range(p_halvings + 1):
        ref_amount = target_reference(p_difficulty_halving_interval, p_zero_bits, p_at_round=r)

        amount = app_client.calculate_target(
            zero_bits=p_zero_bits, difficulty_halving_interval=p_difficulty_halving_interval, last_round=0, at_round=r
        ).return_value

        assert ref_amount == amount, "Target does not match sympy reference calculation"
