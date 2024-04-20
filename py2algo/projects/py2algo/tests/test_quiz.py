import algokit_utils
import pytest
from algokit_utils import get_localnet_default_account
from algokit_utils.config import config
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient

from smart_contracts.artifacts.quiz.client import QuizClient


@pytest.fixture(scope="session")
def app_client(algod_client: AlgodClient, indexer_client: IndexerClient) -> QuizClient:
    config.configure(
        debug=True,
        # trace_all=True,
    )

    client = QuizClient(
        algod_client,
        creator=get_localnet_default_account(algod_client),
        indexer_client=indexer_client,
    )

    client.deploy(
        on_schema_break=algokit_utils.OnSchemaBreak.AppendApp,
        on_update=algokit_utils.OnUpdate.AppendApp,
    )
    return client


def test_question_one(app_client: QuizClient) -> None:
    """Tests the question_one() method."""
    assert app_client.question_one().return_value == 20
