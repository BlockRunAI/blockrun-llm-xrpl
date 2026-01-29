"""XRPL wallet utilities for BlockRun SDK."""

import os
from typing import Optional, Tuple
from pathlib import Path

from xrpl.wallet import Wallet
from xrpl.clients import JsonRpcClient
from xrpl.models import AccountInfo, AccountLines

# XRPL mainnet RPC
XRPL_RPC_URL = "https://xrplcluster.com"

# RLUSD issuer on XRPL mainnet
RLUSD_ISSUER = "rMxCKbEDwqr76QuheSUMdEGf4B9xJ8m5De"
RLUSD_CURRENCY_HEX = "524C555344000000000000000000000000000000"


def create_wallet() -> Tuple[str, str]:
    """
    Create a new XRPL wallet.

    Returns:
        Tuple of (address, seed)
    """
    wallet = Wallet.create()
    return wallet.classic_address, wallet.seed


def load_wallet(seed: Optional[str] = None) -> Wallet:
    """
    Load an XRPL wallet from seed.

    Args:
        seed: XRPL wallet seed. If not provided, uses BLOCKRUN_XRPL_SEED env var.

    Returns:
        XRPL Wallet instance
    """
    if seed is None:
        seed = os.environ.get("BLOCKRUN_XRPL_SEED")

    if not seed:
        raise ValueError(
            "XRPL seed required. Set BLOCKRUN_XRPL_SEED environment variable "
            "or pass seed to the function."
        )

    return Wallet.from_seed(seed)


def get_wallet_address(seed: Optional[str] = None) -> str:
    """Get the wallet address from seed."""
    wallet = load_wallet(seed)
    return wallet.classic_address


def get_xrp_balance(address: str, rpc_url: str = XRPL_RPC_URL) -> float:
    """
    Get XRP balance for an address.

    Args:
        address: XRPL address
        rpc_url: XRPL RPC endpoint

    Returns:
        XRP balance as float
    """
    client = JsonRpcClient(rpc_url)
    response = client.request(AccountInfo(account=address))

    if not response.is_successful():
        return 0.0

    drops = int(response.result["account_data"]["Balance"])
    return drops / 1_000_000


def get_rlusd_balance(address: str, rpc_url: str = XRPL_RPC_URL) -> float:
    """
    Get RLUSD balance for an address.

    Args:
        address: XRPL address
        rpc_url: XRPL RPC endpoint

    Returns:
        RLUSD balance as float
    """
    client = JsonRpcClient(rpc_url)
    response = client.request(AccountLines(account=address))

    if not response.is_successful():
        return 0.0

    for line in response.result.get("lines", []):
        if line.get("account") == RLUSD_ISSUER:
            return float(line.get("balance", 0))

    return 0.0


def get_balances(address: str, rpc_url: str = XRPL_RPC_URL) -> dict:
    """
    Get all balances for an address.

    Returns:
        Dict with 'xrp' and 'rlusd' balances
    """
    return {
        "xrp": get_xrp_balance(address, rpc_url),
        "rlusd": get_rlusd_balance(address, rpc_url),
    }
