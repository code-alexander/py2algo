# import base64
# import sys
# import time
# from pathlib import Path

# from algokit_utils import (
#     TransactionParameters,
#     TransferParameters,
#     get_algod_client,
#     get_indexer_client,
#     get_localnet_default_account,
#     transfer,
# )
# from algosdk import encoding
# from algosdk.atomic_transaction_composer import (
#     AccountTransactionSigner,
#     TransactionWithSigner,
# )
# from algosdk.transaction import PaymentTxn, SuggestedParams
# from algosdk.util import algos_to_microalgos
# from algosdk.v2client.algod import AlgodClient
# from algosdk.v2client.indexer import IndexerClient
# from dotenv import load_dotenv

# base_path = Path(__file__).parent.parent.parent

# sys.path.append(base_path.as_posix())

# from smart_contracts.artifacts.venture_funding.venture_funding_client import VentureFundingClient

# load_dotenv(base_path / ".env.localnet")

# algod_client = get_algod_client()
# indexer_client = get_indexer_client()
# account = get_localnet_default_account(algod_client)


# def flat_fee(algod_client: AlgodClient, fee: int) -> SuggestedParams:
#     sp = algod_client.suggested_params()
#     sp.fee = fee
#     sp.flat_fee = True
#     return sp
