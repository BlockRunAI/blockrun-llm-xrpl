# BlockRun XRPL SDK

Pay-per-request access to GPT-5.2, GPT-5.2 Codex, Claude Opus 4.6, Gemini 3 Pro, Grok 4, and 38+ models via x402 micropayments on XRPL with RLUSD.

> 🆓 **Includes 9 fully-free NVIDIA-hosted models** — DeepSeek V4 Pro/Flash (1M context), Nemotron Nano Omni (vision), Qwen3, Llama 4, GLM-4.7, Mistral. Zero RLUSD, no rate-limit gimmicks. Use `routing_profile="free"` or call any `nvidia/*` model directly.

> **Other Chains:** For Base (USDC) payments, use [blockrun-llm](https://pypi.org/project/blockrun-llm/)

| Feature | This SDK | blockrun-llm |
|---------|----------|--------------|
| **Chain** | XRPL | Base |
| **Payment** | RLUSD | USDC |
| **Wallet** | XRPL seed (s...) | EVM private key (0x...) |
| **Chat** | ✅ | ✅ |
| **Image generation** (DALL-E, Grok Imagine, Nano Banana) | ❌ | ✅ |
| **Video generation** (Grok Imagine Video) | ❌ | ✅ |
| **Music generation** (MiniMax) | ❌ | ✅ |

> **Image + Video + Music generation require Base chain.** Use [blockrun-llm](https://pypi.org/project/blockrun-llm/) (`ImageClient`, `VideoClient`, `MusicClient`) for those endpoints.

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

### Try It Free (No RLUSD Required)

Want to kick the tires before funding a wallet? Route to BlockRun's free NVIDIA tier:

```python
from blockrun_llm_xrpl import LLMClient

client = LLMClient()  # Wallet still required for signing, but $0 charged

# Option 1: call a free model directly
response = client.chat("nvidia/qwen3-next-80b-a3b-thinking", "Explain x402 in 1 sentence")

# Option 2: let the smart router pick the best free model per request
result = client.smart_chat("What is 2+2?", routing_profile="free")
print(result.model)     # e.g. 'nvidia/deepseek-v4-flash'
print(result.response)  # '4'
```

**Available free models** (input + output both $0, all NVIDIA-hosted, last refreshed 2026-04-28):

| Model ID | Context | Best For |
|----------|---------|----------|
| `nvidia/deepseek-v4-pro` | 1M | Flagship reasoning — MMLU-Pro 87.5, GPQA 90.1, SWE-bench 80.6, LiveCodeBench 93.5 |
| `nvidia/deepseek-v4-flash` | 1M | ~5× faster than V4 Pro — chat, summarization, light reasoning (weaker factual recall) |
| `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning` | 256K | Only vision-capable free model — text + images + video (≤2 min) + audio (≤1 hr) |
| `nvidia/qwen3-next-80b-a3b-thinking` | 131K | 116 tok/s reasoning with thinking mode |
| `nvidia/mistral-small-4-119b` | 131K | 114 tok/s — fastest free chat |
| `nvidia/glm-4.7` | 131K | 237 tok/s — GLM-4.7 with thinking mode |
| `nvidia/llama-4-maverick` | 131K | Meta Llama 4 Maverick MoE |
| `nvidia/qwen3-coder-480b` | 131K | Coding-optimised 480B MoE |
| `nvidia/deepseek-v3.2` | 131K | Legacy V3.2 — auto-upgrades to V4 Pro via fallback |

> Note: `nvidia/gpt-oss-120b` and `nvidia/gpt-oss-20b` were retired 2026-04-28 — NVIDIA's free build.nvidia.com tier reserves the right to use prompts/outputs for service improvement, which conflicts with our data-privacy policy.

## Smart Routing (ClawRouter)

Let the SDK automatically pick the cheapest capable model for each request:

```python
from blockrun_llm_xrpl import LLMClient

client = LLMClient()

# Auto-routes to cheapest capable model
result = client.smart_chat("What is 2+2?")
print(result.response)  # '4'
print(result.model)     # 'moonshot/kimi-k2.5' (cheap, fast — AUTO Simple pick)
print(f"Saved {result.routing.savings * 100:.0f}%")  # 'Saved 94%'

# Complex reasoning task -> routes to reasoning model
result = client.smart_chat("Prove the Riemann hypothesis step by step")
print(result.model)  # 'xai/grok-4-1-fast-reasoning'
```

### Routing Profiles

| Profile | Description | Best For |
|---------|-------------|----------|
| `free` | NVIDIA free tier — smart-routes across 9 models (DeepSeek V4 Pro/Flash, Nemotron Nano Omni, Qwen3, GLM-4.7, Llama 4, Mistral) | Zero-cost testing, dev, prod |
| `eco` | Cheapest models per tier (DeepSeek, xAI) | Cost-sensitive production |
| `auto` | Best balance of cost/quality (default) | General use |
| `premium` | Top-tier models (OpenAI, Anthropic) | Quality-critical tasks |

```python
# Use premium models for complex tasks
result = client.smart_chat(
    "Write production-grade async Python code",
    routing_profile="premium"
)
print(result.model)  # 'openai/gpt-5.2-codex' (coding) or 'anthropic/claude-opus-4.6' (architecture)
```

### How It Works

ClawRouter uses a 14-dimension rule-based classifier to analyze each request:

- **Token count** - Short vs long prompts
- **Code presence** - Programming keywords
- **Reasoning markers** - "prove", "step by step", etc.
- **Technical terms** - Architecture, optimization, etc.
- **Creative markers** - Story, poem, brainstorm, etc.
- **Agentic patterns** - Multi-step, tool use indicators

The classifier runs in <1ms, 100% locally, and routes to one of four tiers:

| Tier | Example Tasks | Auto Profile Model |
|------|---------------|-------------------|
| SIMPLE | "What is 2+2?", definitions | moonshot/kimi-k2.5 |
| MEDIUM | Code snippets, explanations | xai/grok-code-fast-1 |
| COMPLEX | Architecture, long documents | google/gemini-3-pro-preview |
| REASONING | Proofs, multi-step reasoning | xai/grok-4-1-fast-reasoning |

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

# Use Codex for coding (cost-effective)
response = client.chat(
    "openai/gpt-5.2-codex",
    "Write a binary search tree in Python"
)

# With system prompt
response = client.chat(
    "anthropic/claude-opus-4.6",
    "Design a microservices architecture",
    system="You are a senior software architect."
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

All 38+ models from BlockRun are available:

- **OpenAI**: gpt-5.2, gpt-5.2-codex, gpt-4o, gpt-4o-mini, o1, o3, o4-mini
- **Anthropic**: claude-opus-4.6, claude-opus-4.5, claude-opus-4, claude-sonnet-4.6, claude-sonnet-4, claude-haiku-4.5
- **Google**: gemini-3-pro-preview, gemini-2.5-pro, gemini-2.5-flash
- **DeepSeek**: deepseek-chat, deepseek-reasoner
- **xAI**: grok-4-1-fast-reasoning, grok-4-fast-reasoning, grok-3, grok-3-mini, grok-code-fast-1
- **NVIDIA (all FREE)**: deepseek-v4-pro, deepseek-v4-flash, nemotron-3-nano-omni-30b-a3b-reasoning (vision), qwen3-next-80b-a3b-thinking, mistral-small-4-119b, glm-4.7, llama-4-maverick, qwen3-coder-480b, deepseek-v3.2
- **Moonshot**: kimi-k2.6 (flagship — vision + reasoning_content), kimi-k2.5 (legacy)

**Latest Additions:**
- **Claude Opus 4.6** - Latest flagship with 64k output
- **GPT-5.2 Codex** - Optimized for code generation
- **Kimi K2.6** - 256k context, multi-modal (vision + text), returns reasoning_content. K2.5 still available as `moonshot/kimi-k2.5`.

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
- [Documentation](https://github.com/BlockRunAI/awesome-blockrun/tree/main/docs)
- [GitHub](https://github.com/BlockRunAI/blockrun-llm-xrpl)
- [Telegram](https://t.me/+mroQv4-4hGgzOGUx)

## License

MIT
