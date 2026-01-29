"""
BlockRun XRPL SDK - Pay-per-request AI via x402 on XRPL with RLUSD

Example:
    from blockrun_llm_xrpl import LLMClient

    client = LLMClient()  # Uses BLOCKRUN_XRPL_SEED from env
    response = client.chat("openai/gpt-4o-mini", "Hello!")
    print(response)

Async usage:
    from blockrun_llm_xrpl import AsyncLLMClient

    async with AsyncLLMClient() as client:
        response = await client.chat("openai/gpt-4o-mini", "Hello!")
        print(response)
"""

from .client import LLMClient, AsyncLLMClient, XRPL_API_URL
from .types import (
    ChatMessage,
    ChatResponse,
    Model,
    APIError,
    PaymentError,
)
from .wallet import (
    create_wallet,
    load_wallet,
    get_wallet_address,
    get_xrp_balance,
    get_rlusd_balance,
    get_balances,
    RLUSD_ISSUER,
    XRPL_RPC_URL,
)

__version__ = "0.1.0"
__all__ = [
    "LLMClient",
    "AsyncLLMClient",
    "XRPL_API_URL",
    "ChatMessage",
    "ChatResponse",
    "Model",
    "APIError",
    "PaymentError",
    "create_wallet",
    "load_wallet",
    "get_wallet_address",
    "get_xrp_balance",
    "get_rlusd_balance",
    "get_balances",
    "RLUSD_ISSUER",
    "XRPL_RPC_URL",
]
