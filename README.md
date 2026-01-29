# BlockRun XRPL SDK

Pay-per-request access to GPT-5.2, Claude 4, Gemini 2.5, Grok, and more via x402 micropayments on XRPL with RLUSD.

## Installation

```bash
pip install blockrun-llm-xrpl
```

## Quick Start

```python
from blockrun_llm_xrpl import LLMClient

client = LLMClient()  # Uses BLOCKRUN_XRPL_SEED from env
response = client.chat("openai/gpt-4o-mini", "Hello!")
print(response)
```

That's it. The SDK handles x402 payment with RLUSD automatically.

## How It Works

1. You send a request to BlockRun's XRPL API
2. The API returns a 402 Payment Required with the price
3. The SDK automatically signs an RLUSD payment on XRPL
4. The request is retried with the payment proof
5. The t54.ai facilitator settles the payment
6. You receive the AI response

**Your seed never leaves your machine** - it's only used for local signing.

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `BLOCKRUN_XRPL_SEED` | Your XRPL wallet seed | Yes (or pass to constructor) |

## Setting Up Your Wallet

1. Create an XRPL wallet (or use existing one)
2. Fund it with XRP for transaction fees (~1 XRP is plenty)
3. Set up a trust line to RLUSD issuer
4. Get some RLUSD for API payments
5. Export your seed and set it as `BLOCKRUN_XRPL_SEED`

```bash
# .env file
BLOCKRUN_XRPL_SEED=sEd...your_seed_here
```

### Create a New Wallet

```python
from blockrun_llm_xrpl import create_wallet

address, seed = create_wallet()
print(f"Address: {address}")
print(f"Seed: {seed}")  # Save this securely!
```

### Check Balances

```python
from blockrun_llm_xrpl import LLMClient

client = LLMClient()
print(f"RLUSD Balance: {client.get_balance()}")
```

## Usage Examples

### Simple Chat

```python
from blockrun_llm_xrpl import LLMClient

client = LLMClient()

response = client.chat("openai/gpt-4o", "Explain quantum computing")
print(response)

# With system prompt
response = client.chat(
    "anthropic/claude-sonnet-4",
    "Write a haiku",
    system="You are a creative poet."
)
```

### Full Chat Completion

```python
from blockrun_llm_xrpl import LLMClient

client = LLMClient()

messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "How do I read a file in Python?"}
]

result = client.chat_completion("openai/gpt-4o-mini", messages)
print(result.choices[0].message.content)
```

### Check Spending

```python
from blockrun_llm_xrpl import LLMClient

client = LLMClient()

response = client.chat("openai/gpt-4o-mini", "Hello!")
print(response)

spending = client.get_spending()
print(f"Spent ${spending['total_usd']:.4f} across {spending['calls']} calls")
```

### Async Usage

```python
import asyncio
from blockrun_llm_xrpl import AsyncLLMClient

async def main():
    async with AsyncLLMClient() as client:
        response = await client.chat("openai/gpt-4o-mini", "Hello!")
        print(response)

        # Multiple requests concurrently
        tasks = [
            client.chat("openai/gpt-4o-mini", "What is 2+2?"),
            client.chat("openai/gpt-4o-mini", "What is 3+3?"),
        ]
        responses = await asyncio.gather(*tasks)
        for r in responses:
            print(r)

asyncio.run(main())
```

## Available Models

All models from BlockRun are available:

- OpenAI: gpt-5.2, gpt-5-mini, gpt-4o, gpt-4o-mini, o1, o3, etc.
- Anthropic: claude-opus-4.5, claude-sonnet-4, claude-haiku-4.5
- Google: gemini-3-pro-preview, gemini-2.5-pro, gemini-2.5-flash
- DeepSeek: deepseek-chat, deepseek-reasoner
- xAI: grok-3, grok-3-fast, grok-3-mini

## Error Handling

```python
from blockrun_llm_xrpl import LLMClient, APIError, PaymentError

client = LLMClient()

try:
    response = client.chat("openai/gpt-4o-mini", "Hello!")
except PaymentError as e:
    print(f"Payment failed: {e}")
    # Check your RLUSD balance
except APIError as e:
    print(f"API error ({e.status_code}): {e}")
```

## Security

- **Seed stays local**: Your seed is only used for signing on your machine
- **No custody**: BlockRun never holds your funds
- **Verify transactions**: All payments are on-chain and verifiable on XRPL

## Links

- [Website](https://blockrun.ai)
- [Documentation](https://docs.blockrun.ai)
- [GitHub](https://github.com/BlockRunAI/blockrun-llm-xrpl)

## License

MIT
