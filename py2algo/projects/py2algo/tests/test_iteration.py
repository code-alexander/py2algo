import algokit_utils
import pytest
from algokit_utils import get_localnet_default_account
from algokit_utils.config import config
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient

from smart_contracts.artifacts.iteration.client import IterationClient


@pytest.fixture(scope="session")
def iteration_client(algod_client: AlgodClient, indexer_client: IndexerClient) -> IterationClient:
    config.configure(
        debug=True,
        # trace_all=True,
    )

    client = IterationClient(
        algod_client,
        creator=get_localnet_default_account(algod_client),
        indexer_client=indexer_client,
    )

    client.deploy(
        on_schema_break=algokit_utils.OnSchemaBreak.AppendApp,
        on_update=algokit_utils.OnUpdate.AppendApp,
    )
    return client


@pytest.mark.parametrize(
    "array, total",
    [
        ([], 0),
        ([1], 1),
        ([1, 2, 3, 4, 5], 15),
    ],
)
def test_sum_array(iteration_client: IterationClient, array: list[int], total: int) -> None:
    """Tests the sum_array() method."""
    assert iteration_client.sum(array=array).return_value == total


@pytest.mark.parametrize(
    "array, n",
    [
        ([], 0),
        ([1], 0),
        ([1, 2, 3, 4, 5], 2),
    ],
)
def test_first_even(iteration_client: IterationClient, array: list[int], n: int) -> None:
    """Tests the first_even() method."""
    assert iteration_client.first_even(array=array).return_value == n


@pytest.mark.parametrize(
    "array, index",
    [
        ([], 0),
        ([1], 0),
        ([1, 2, 3, 4, 5], 3),
    ],
)
def test_last_even_index(iteration_client: IterationClient, array: list[int], index: int) -> None:
    """Tests the last_even_index() method."""
    assert iteration_client.last_even_index(array=array).return_value == index


@pytest.mark.parametrize(
    "string, times, result",
    [
        ("", 0, ""),
        ("a", 0, ""),
        ("a", 1, "a"),
        ("a", 3, "aaa"),
    ],
)
def test_repeat(iteration_client: IterationClient, string: str, times: int, result: str) -> None:
    """Tests the repeat() method."""
    assert iteration_client.repeat(string=string, times=times).return_value == result


@pytest.mark.parametrize(
    "n, expected",
    [
        (0, 0),
        (1, 1),
        (2, 1),
        (3, 2),
        (4, 3),
        (5, 5),
        (6, 8),
        (7, 13),
    ],
)
def test_fibonacci(iteration_client: IterationClient, n: int, expected: int) -> None:
    """Tests the fibonacci() method."""
    assert iteration_client.fibonacci(n=n).return_value == expected
