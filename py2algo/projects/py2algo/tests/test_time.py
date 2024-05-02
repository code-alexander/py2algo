from datetime import datetime, timezone

import algokit_utils
import pytest
from algokit_utils import (
    get_localnet_default_account,
)
from algokit_utils.config import config
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient
from hypothesis import given, settings
from hypothesis import strategies as st

from smart_contracts.artifacts.time.client import TimeClient


@pytest.fixture(scope="session")
def app_client(algod_client: AlgodClient, indexer_client: IndexerClient) -> TimeClient:
    config.configure(
        debug=True,
        # trace_all=True,
    )

    account = get_localnet_default_account(algod_client)

    client = TimeClient(
        algod_client,
        creator=account,
        indexer_client=indexer_client,
    )

    client.deploy(
        on_schema_break=algokit_utils.OnSchemaBreak.AppendApp,
        on_update=algokit_utils.OnUpdate.AppendApp,
    )

    return client


@settings(deadline=None)
@given(st.datetimes(min_value=datetime(1970, 1, 1)))
def test_to_date(app_client: TimeClient, _datetime: datetime) -> None:
    """Tests the `to_date` method.

    Args:
        app_client (TimeClient): The smart contract app client.
        _datetime (datetime): The datetime to test.
    """
    dt = _datetime.replace(tzinfo=timezone.utc)
    app_value = tuple(app_client.to_date(timestamp=int(dt.timestamp())).return_value)
    reference_value = (dt.year, dt.month, dt.day)
    assert app_value == reference_value
