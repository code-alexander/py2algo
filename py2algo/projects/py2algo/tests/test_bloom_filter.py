import algokit_utils
import pytest
from algokit_utils import (
    Account,
    CreateTransactionParameters,
    TransactionParameters,
    TransferParameters,
    transfer,
)
from algokit_utils.config import config
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient

from smart_contracts.artifacts.bloom_filter.client import BloomFilterClient


@pytest.fixture(scope="session")
def app_client(account: Account, algod_client: AlgodClient, indexer_client: IndexerClient) -> BloomFilterClient:
    config.configure(
        debug=True,
        # trace_all=True,
    )

    client = BloomFilterClient(
        algod_client,
        creator=account,
        indexer_client=indexer_client,
    )

    client.create_new(
        max_supply=10_000,
    )

    transfer(
        algod_client,
        TransferParameters(
            from_account=account,
            to_address=client.app_address,
            micro_algos=100_000_000,
        ),
    )

    client.create_bloom_filter(
        transaction_parameters=CreateTransactionParameters(boxes=[(0, "bloom"), (0, ""), (0, ""), (0, "")])
    )

    return client


def test_buy_nft(app_client: BloomFilterClient) -> None:
    """Tests the buy_nft() method."""

    # Mint first NFT
    app_client.buy_nft(
        unit_name="The GOAT",
        transaction_parameters=TransactionParameters(boxes=[(0, "bloom"), (0, ""), (0, ""), (0, "")]),
    )

    # Make sure an error is raised when trying to mint a second NFT with the same unit name
    with pytest.raises(algokit_utils.logic_error.LogicError):
        app_client.buy_nft(
            unit_name="The GOAT",
            transaction_parameters=TransactionParameters(boxes=[(0, "bloom"), (0, ""), (0, ""), (0, "")]),
        )
