"""XRPL LLM Client for BlockRun API with x402 payments."""

import os
import json
import base64
from typing import Optional, List, Dict, Any, Union

import httpx
from xrpl.wallet import Wallet
from x402_xrpl.client import XRPLPresignedPaymentPayer, XRPLPresignedPaymentPayerOptions
from x402_xrpl import PaymentRequirements

from .types import ChatMessage, ChatResponse, APIError, PaymentError
from .wallet import load_wallet, get_rlusd_balance, RLUSD_ISSUER, RLUSD_CURRENCY_HEX, XRPL_RPC_URL

# BlockRun XRPL API
XRPL_API_URL = "https://xrpl.blockrun.ai/api"

# XRPL Network
XRPL_NETWORK = "xrpl:0"  # mainnet


class LLMClient:
    """
    BlockRun LLM Client for XRPL (RLUSD payments).

    Example:
        from blockrun_llm_xrpl import LLMClient

        client = LLMClient()  # Uses BLOCKRUN_XRPL_SEED from env
        response = client.chat("openai/gpt-4o-mini", "Hello!")
        print(response)
    """

    def __init__(
        self,
        seed: Optional[str] = None,
        api_url: str = XRPL_API_URL,
        rpc_url: str = XRPL_RPC_URL,
        timeout: float = 60.0,
    ):
        """
        Initialize the XRPL LLM client.

        Args:
            seed: XRPL wallet seed. If not provided, uses BLOCKRUN_XRPL_SEED env var.
            api_url: BlockRun API URL (default: https://xrpl.blockrun.ai/api)
            rpc_url: XRPL RPC URL for autofill (default: https://xrplcluster.com)
            timeout: Request timeout in seconds
        """
        self.wallet = load_wallet(seed)
        self.api_url = api_url.rstrip("/")
        self.rpc_url = rpc_url
        self.timeout = timeout
        self._http_client = httpx.Client(timeout=timeout)

        # Initialize x402 payment payer
        payer_options = XRPLPresignedPaymentPayerOptions(
            wallet=self.wallet,
            network=XRPL_NETWORK,
            rpc_url=rpc_url,
        )
        self._payer = XRPLPresignedPaymentPayer(payer_options)

        # Spending tracking
        self._total_spent = 0.0
        self._call_count = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """Close the HTTP client."""
        self._http_client.close()

    @property
    def address(self) -> str:
        """Get the wallet address."""
        return self.wallet.classic_address

    def get_balance(self) -> float:
        """Get RLUSD balance."""
        return get_rlusd_balance(self.address, self.rpc_url)

    def get_spending(self) -> Dict[str, Any]:
        """Get spending summary for this session."""
        return {
            "total_usd": self._total_spent,
            "calls": self._call_count,
        }

    def chat(
        self,
        model: str,
        message: str,
        system: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Simple chat interface - send a message, get a response.

        Args:
            model: Model ID (e.g., "openai/gpt-4o-mini")
            message: User message
            system: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Assistant's response text
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": message})

        response = self.chat_completion(model, messages, max_tokens, temperature)
        return response.choices[0].message.content

    def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int = 1024,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
    ) -> ChatResponse:
        """
        Full chat completion API.

        Args:
            model: Model ID
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Top-p sampling

        Returns:
            ChatResponse object
        """
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "stream": False,
        }
        if temperature is not None:
            payload["temperature"] = temperature
        if top_p is not None:
            payload["top_p"] = top_p

        url = f"{self.api_url}/v1/chat/completions"

        # Step 1: Initial request to get 402 payment requirements
        response = self._http_client.post(url, json=payload)

        if response.status_code == 402:
            # Parse payment requirements
            payment_required = self._parse_402_response(response)

            # Create and sign payment using x402-xrpl library
            payment_header = self._create_payment(payment_required)

            # Step 2: Retry with payment
            response = self._http_client.post(
                url,
                json=payload,
                headers={"X-Payment": payment_header},
            )

        if response.status_code != 200:
            error_data = response.json() if response.content else {}
            raise APIError(
                error_data.get("error", f"Request failed with status {response.status_code}"),
                response.status_code,
                error_data,
            )

        # Track spending
        self._call_count += 1

        data = response.json()
        return ChatResponse(**data)

    def _parse_402_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Parse 402 Payment Required response."""
        # Try X-Payment-Required header first
        payment_required_b64 = response.headers.get("X-Payment-Required")
        if not payment_required_b64:
            payment_required_b64 = response.headers.get("PAYMENT-REQUIRED")

        if payment_required_b64:
            return json.loads(base64.b64decode(payment_required_b64))

        # Fallback to response body
        data = response.json()
        if "accepts" in data:
            return data

        raise PaymentError("Could not parse payment requirements from 402 response")

    def _create_payment(self, payment_required: Dict[str, Any]) -> str:
        """
        Create a signed XRPL payment authorization for x402.

        Uses the official x402-xrpl library for proper payment header creation.

        Args:
            payment_required: Parsed 402 payment requirements

        Returns:
            Base64-encoded payment header
        """
        accepts = payment_required.get("accepts", [])
        if not accepts:
            raise PaymentError("No payment options in 402 response")

        # Use first accepted payment option
        option = accepts[0]
        extra = option.get("extra", {})
        invoice_id = extra.get("invoiceId", "")

        if not invoice_id:
            raise PaymentError("Invalid payment requirements: missing invoiceId in extra")

        # Track spending
        amount = float(option.get("amount", 0))
        self._total_spent += amount

        # Create PaymentRequirements for x402-xrpl library
        req = PaymentRequirements(
            scheme=option.get("scheme", "exact"),
            network=option.get("network", XRPL_NETWORK),
            amount=option.get("amount"),
            asset=option.get("asset"),
            pay_to=option.get("payTo"),
            max_timeout_seconds=option.get("maxTimeoutSeconds", 300),
            extra=extra,
        )

        # Create payment header using x402-xrpl library
        return self._payer.create_payment_header(req, invoice_id=invoice_id)

    def list_models(self) -> List[Dict[str, Any]]:
        """List available models."""
        response = self._http_client.get(f"{self.api_url}/v1/models")
        if response.status_code != 200:
            raise APIError("Failed to list models", response.status_code)
        data = response.json()
        return data.get("data", data.get("models", []))


class AsyncLLMClient:
    """
    Async BlockRun LLM Client for XRPL (RLUSD payments).

    Example:
        from blockrun_llm_xrpl import AsyncLLMClient

        async with AsyncLLMClient() as client:
            response = await client.chat("openai/gpt-4o-mini", "Hello!")
            print(response)
    """

    def __init__(
        self,
        seed: Optional[str] = None,
        api_url: str = XRPL_API_URL,
        rpc_url: str = XRPL_RPC_URL,
        timeout: float = 60.0,
    ):
        self.wallet = load_wallet(seed)
        self.api_url = api_url.rstrip("/")
        self.rpc_url = rpc_url
        self.timeout = timeout
        self._http_client = httpx.AsyncClient(timeout=timeout)

        # Initialize x402 payment payer
        payer_options = XRPLPresignedPaymentPayerOptions(
            wallet=self.wallet,
            network=XRPL_NETWORK,
            rpc_url=rpc_url,
        )
        self._payer = XRPLPresignedPaymentPayer(payer_options)

        self._total_spent = 0.0
        self._call_count = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        await self._http_client.aclose()

    @property
    def address(self) -> str:
        return self.wallet.classic_address

    def get_balance(self) -> float:
        return get_rlusd_balance(self.address, self.rpc_url)

    def get_spending(self) -> Dict[str, Any]:
        return {"total_usd": self._total_spent, "calls": self._call_count}

    async def chat(
        self,
        model: str,
        message: str,
        system: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: Optional[float] = None,
    ) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": message})

        response = await self.chat_completion(model, messages, max_tokens, temperature)
        return response.choices[0].message.content

    async def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int = 1024,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
    ) -> ChatResponse:
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "stream": False,
        }
        if temperature is not None:
            payload["temperature"] = temperature
        if top_p is not None:
            payload["top_p"] = top_p

        url = f"{self.api_url}/v1/chat/completions"

        response = await self._http_client.post(url, json=payload)

        if response.status_code == 402:
            payment_required = self._parse_402_response(response)
            payment_header = self._create_payment(payment_required)

            response = await self._http_client.post(
                url,
                json=payload,
                headers={"X-Payment": payment_header},
            )

        if response.status_code != 200:
            error_data = response.json() if response.content else {}
            raise APIError(
                error_data.get("error", f"Request failed with status {response.status_code}"),
                response.status_code,
                error_data,
            )

        self._call_count += 1
        data = response.json()
        return ChatResponse(**data)

    def _parse_402_response(self, response: httpx.Response) -> Dict[str, Any]:
        payment_required_b64 = response.headers.get("X-Payment-Required")
        if not payment_required_b64:
            payment_required_b64 = response.headers.get("PAYMENT-REQUIRED")

        if payment_required_b64:
            return json.loads(base64.b64decode(payment_required_b64))

        data = response.json()
        if "accepts" in data:
            return data

        raise PaymentError("Could not parse payment requirements from 402 response")

    def _create_payment(self, payment_required: Dict[str, Any]) -> str:
        """Create payment using x402-xrpl library."""
        accepts = payment_required.get("accepts", [])
        if not accepts:
            raise PaymentError("No payment options in 402 response")

        option = accepts[0]
        extra = option.get("extra", {})
        invoice_id = extra.get("invoiceId", "")

        if not invoice_id:
            raise PaymentError("Invalid payment requirements: missing invoiceId in extra")

        # Track spending
        amount = float(option.get("amount", 0))
        self._total_spent += amount

        # Create PaymentRequirements for x402-xrpl library
        req = PaymentRequirements(
            scheme=option.get("scheme", "exact"),
            network=option.get("network", XRPL_NETWORK),
            amount=option.get("amount"),
            asset=option.get("asset"),
            pay_to=option.get("payTo"),
            max_timeout_seconds=option.get("maxTimeoutSeconds", 300),
            extra=extra,
        )

        return self._payer.create_payment_header(req, invoice_id=invoice_id)

    async def list_models(self) -> List[Dict[str, Any]]:
        response = await self._http_client.get(f"{self.api_url}/v1/models")
        if response.status_code != 200:
            raise APIError("Failed to list models", response.status_code)
        data = response.json()
        return data.get("data", data.get("models", []))
