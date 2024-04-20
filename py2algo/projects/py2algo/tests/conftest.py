from pathlib import Path

import pytest
from algokit_utils import Account, get_algod_client, get_indexer_client, get_localnet_default_account, is_localnet
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient
from dotenv import load_dotenv


@pytest.fixture(autouse=True, scope="session")
def environment_fixture() -> None:
    env_path = Path(__file__).parent.parent / ".env.localnet"
    load_dotenv(env_path)


@pytest.fixture(scope="session")
def algod_client() -> AlgodClient:
    client = get_algod_client()

    # you can remove this assertion to test on other networks,
    # included here to prevent accidentally running against other networks
    assert is_localnet(client)
    return client


@pytest.fixture(scope="session")
def indexer_client() -> IndexerClient:
    return get_indexer_client()


@pytest.fixture(scope="session")
def account(algod_client: AlgodClient) -> Account:
    return get_localnet_default_account(algod_client)
