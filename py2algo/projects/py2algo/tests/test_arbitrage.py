import pytest
from algokit_utils import (
    Account,
    EnsureBalanceParameters,
    ensure_funded,
    get_account,
)
from algokit_utils.config import config
from algokit_utils.logic_error import LogicError
from algosdk.atomic_transaction_composer import (
    AccountTransactionSigner,
    TransactionWithSigner,
)
from algosdk.transaction import PaymentTxn
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient

from smart_contracts.artifacts.arbitrage.client import BalanceProtectorClient


@pytest.fixture(scope="function")
def app_client(account: Account, algod_client: AlgodClient, indexer_client: IndexerClient) -> BalanceProtectorClient:
    config.configure(
        debug=True,
        # trace_all=True,
    )

    client = BalanceProtectorClient(
        algod_client,
        creator=account,
        indexer_client=indexer_client,
    )
    client.create_new(owner=account.address)
    return client


def test_profitable_trade_succeeds(app_client: BalanceProtectorClient, account: Account, algod_client: AlgodClient):
    """Simulates a profitable trade by transferring funds from another account."""

    balance = lambda a: algod_client.account_info(a.address)["amount"]
    balance_before = balance(account)

    # Get or create a new account for testing
    counterparty = get_account(algod_client, "counterparty")

    ensure_funded(
        algod_client,
        EnsureBalanceParameters(
            account_to_fund=counterparty,
            min_spending_balance_micro_algos=10_000,
        ),
    )

    txn = PaymentTxn(
        sender=counterparty.address,
        receiver=account.address,
        amt=10_000,
        sp=algod_client.suggested_params(),
    )
    tws = TransactionWithSigner(txn, AccountTransactionSigner(counterparty.private_key))

    atc = app_client.compose().take_snapshot(asset=0).build()
    atc = atc.add_transaction(tws)
    atc = app_client.compose(atc).protect().build()

    result = app_client.compose(atc).execute()

    balance_after = balance(account)

    assert balance_after >= balance_before, "Balance should be protected"
    assert result.confirmed_round > 0, "Transaction should be confirmed"


def test_unprofitable_trade_fails(app_client: BalanceProtectorClient):
    """To simulate a losing trade, call the contract methods without making any trades in between."""
    atc = app_client.compose().take_snapshot(asset=0).protect()

    with pytest.raises(LogicError) as e:
        atc.execute()
    assert "would result negative" in str(e.value)
