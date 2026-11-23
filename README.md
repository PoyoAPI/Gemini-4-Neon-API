# Gemini 4 Neon API: cURL, Python, and Node.js Examples

[![Gemini 4 Neon on PoYo](https://img.shields.io/badge/Try%20on%20PoYo-gemini--4--neon-84cc16)](https://poyo.ai/models/gemini-4-neon?utm_source=github&utm_medium=social&utm_campaign=gemini-4-neon-launch) [![API docs](https://img.shields.io/badge/API-docs-22d3ee)](https://docs.poyo.ai/api-manual/chat-series/gemini-native-format?utm_source=github&utm_medium=social&utm_campaign=gemini-4-neon-launch) [![Check](https://github.com/PoyoAPI/Gemini-4-Neon-API/actions/workflows/check.yml/badge.svg)](https://github.com/PoyoAPI/Gemini-4-Neon-API/actions/workflows/check.yml)

Runnable examples for Google **Gemini 4 Neon** through PoYo, in both the OpenAI-compatible Chat Completions format and the Gemini Native `generateContent` format: agentic coding, multi-step agents, knowledge work, and science, with streaming and thinking-level control over a 1M-token context window.

**Answer:** To use the Gemini 4 Neon API, send a server-side request to `POST https://api.poyo.ai/v1/chat/completions` with `"model": "gemini-4-neon"`, or to `POST https://api.poyo.ai/v1beta/models/gemini-4-neon:generateContent`, with a PoYo API key. The examples in this repository run with Python 3.9+, Node.js 22+, or cURL.

Last verified against the live PoYo schema and pricing on **November 23, 2026**.

## Gemini 4 Neon at a glance

- **Model ID:** `gemini-4-neon`
- **Formats:** Chat Completions (`/v1/chat/completions`) and Gemini Native (`/v1beta/models/gemini-4-neon:generateContent` and `:streamGenerateContent`)
- **Context:** 1,048,576 tokens, shared by input, thinking, and output; 64K output tokens per response by default
- **Thinking levels:** `low`, `medium`, `high` (default), and `xhigh`
- **Input:** text, image, audio, video, and PDF; output is text
- **Availability:** released by Google on November 18, 2026
- **Price on PoYo:** $2.40 input, $12.00 output, and $0.12 cache read per 1M tokens, 20% below Google's $3.00 / $15.00 / $0.15

## Quickstart

1. Create a key in the [PoYo dashboard](https://poyo.ai/dashboard/api-key?utm_source=github&utm_medium=social&utm_campaign=gemini-4-neon-launch).
2. Copy `.env.example` to `.env` and replace the placeholder.
3. Run one of the examples. Each prints the model's text and the token usage.

```dotenv
POYO_API_KEY=YOUR_POYO_API_KEY_HERE
POYO_BASE_URL=https://api.poyo.ai
```

### Python

```bash
python python/generate.py                                        # Chat Completions
python python/generate.py payloads/chat-completions-stream.json  # Chat Completions, streaming
python python/generate.py payloads/gemini-native.json            # Gemini Native
python python/generate.py payloads/gemini-native-thinking.json   # Gemini Native, thinkingLevel xhigh
python python/generate.py payloads/gemini-native.json --stream   # Gemini Native streaming
```

[`python/generate.py`](python/generate.py) uses only the Python standard library.

### Node.js

```bash
node node/index.mjs
node node/index.mjs payloads/chat-completions-stream.json
node node/index.mjs payloads/gemini-native-thinking.json
node node/index.mjs payloads/gemini-native.json --stream
```

[`node/index.mjs`](node/index.mjs) has no dependencies and uses the built-in `fetch`.

### cURL

```bash
curl -X POST "https://api.poyo.ai/v1/chat/completions" \
  -H "Authorization: Bearer $POYO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "gemini-4-neon", "messages": [{"role": "user", "content": "Explain the difference between optimistic and pessimistic locking in three sentences."}]}'
```

Streaming, thinking-level, and Gemini Native requests are in [curl/generate.md](curl/generate.md).

### OpenAI SDK

Point the OpenAI SDK at `https://api.poyo.ai/v1`, use your PoYo API key, and set `model` to `gemini-4-neon`.

## Example requests

| File | Format | Task |
| --- | --- | --- |
| [`chat-completions.json`](payloads/chat-completions.json) | Chat Completions | Add retries, backoff, and a timeout to a Node.js `fetch` call, `max_tokens: 2048` |
| [`chat-completions-stream.json`](payloads/chat-completions-stream.json) | Chat Completions | Short explanation streamed with `"stream": true` |
| [`gemini-native.json`](payloads/gemini-native.json) | Gemini Native | JavaScript-to-TypeScript migration plan, `maxOutputTokens: 4096` |
| [`gemini-native-thinking.json`](payloads/gemini-native-thinking.json) | Gemini Native | Debug duplicate Kafka-to-Postgres writes with `thinkingLevel: "xhigh"` |

## Request fields

### Chat Completions

| Field | Requirement | Meaning |
| --- | --- | --- |
| model | required | `gemini-4-neon`. |
| messages | required | `system`, `user`, and `assistant` messages with `content`. |
| max_tokens | optional | Maximum generated tokens. |
| temperature | optional | 0–2. |
| top_p | optional | 0–1. Use either `top_p` or `temperature`. |
| stream | optional | `true` returns server-sent events. |

### Gemini Native

| Field | Requirement | Meaning |
| --- | --- | --- |
| contents | required | Turns with `role` (`user` or `model`) and `parts` (`text` or `inlineData`). |
| generationConfig | optional | `temperature`, `topP`, `topK`, `maxOutputTokens`, `stopSequences`. |
| generationConfig.thinkingConfig.thinkingLevel | optional | `low`, `medium`, `high` (default), or `xhigh`. |
| safetySettings | optional | Category and threshold pairs. |

In Gemini Native, the model ID goes in the URL path. The response is Google's `GenerateContentResponse`: text is in `candidates[].content.parts[].text` and token counts in `usageMetadata`, with thinking tokens in `thoughtsTokenCount`. Thinking parts can carry `thought: true` or a `thoughtSignature` without `text`; skip them when you join the text.

## Thinking levels

Google gives Gemini 4 Neon four thinking levels. Gemini 4 Carbon stops at `high`; Neon adds `xhigh`.

| Level | Use it for |
| --- | --- |
| `low` / `medium` | Interactive coding, UI prototyping, and other latency-sensitive calls |
| `high` (default) | General tool-calling agents and everyday reasoning |
| `xhigh` | Hard architecture, math, science, and multi-step research |

```json
"generationConfig": {
  "maxOutputTokens": 8192,
  "thinkingConfig": { "thinkingLevel": "xhigh" }
}
```

## Pricing

1 credit = $0.005.

| Usage | PoYo | Google list price |
| --- | --- | --- |
| Input | 480 credits ($2.40) per 1M tokens | $3.00 per 1M tokens |
| Output | 2,400 credits ($12.00) per 1M tokens | $15.00 per 1M tokens |
| Cache read | 24 credits ($0.12) per 1M tokens | $0.15 per 1M tokens |

Example: a request with 10,000 input tokens and 2,000 output tokens costs 10,000 × $2.40 / 1M + 2,000 × $12.00 / 1M = $0.048 (9.6 credits). Google counts thinking tokens as output, so higher thinking levels cost more per request. Confirm current prices on the [model page](https://poyo.ai/models/gemini-4-neon?utm_source=github&utm_medium=social&utm_campaign=gemini-4-neon-launch).

## Neon or Carbon?

Gemini 4 Carbon costs less per token on PoYo ($1.60 input / $8.00 output per 1M). Google positions Neon between Gemini 4 Hydrogen and Gemini 4 Carbon as a faster model adapted from Carbon. According to Google DeepMind:

- At the default `high` level, Neon has a 32% lower cost per task than Carbon on the Artificial Analysis Intelligence Index and runs about twice as fast end to end.
- Neon scores 76.0% on AutoBaxBench secure coding, against 74.0% for Carbon.
- Neon scores 95.2% on GraphWalks 256K–1M long-context recall.

Pick Neon when speed, steerable agents, or `xhigh` reasoning matter; benchmark both on your own workload before switching.

## Production guidance

Set an application timeout long enough for `xhigh` thinking, retry only 429 and transient 5xx responses, cap `max_tokens` or `maxOutputTokens`, and record token usage. Do not put `POYO_API_KEY` in browser or mobile client code. LLM responses come back in each format's native shape, so check the HTTP status and the `error` object rather than a `code` field.

## FAQ

**How much does the Gemini 4 Neon API cost?** On PoYo, $2.40 per 1M input tokens, $12.00 per 1M output tokens, and $0.12 per 1M cache-read tokens, 20% below Google's price.

**What are the context window and max output?** A 1,048,576-token context window shared by input, thinking, and output, with 64K output tokens per response by default.

**How do I set the thinking level?** In the Gemini Native format, set `generationConfig.thinkingConfig.thinkingLevel` to `low`, `medium`, `high`, or `xhigh`. Omit it to use `high`.

**Can I use the OpenAI SDK?** Yes. Set the base URL to `https://api.poyo.ai/v1` and `model` to `gemini-4-neon`.

**Does it support streaming?** Yes: `"stream": true` in Chat Completions, or `:streamGenerateContent` in Gemini Native.

## Repository map

- [`payloads/`](payloads) — Chat Completions and Gemini Native request bodies
- [`python/generate.py`](python/generate.py) — standard-library Python example with streaming
- [`node/index.mjs`](node/index.mjs) — dependency-free Node.js example with streaming
- [`curl/generate.md`](curl/generate.md) — copy-paste cURL requests, including streaming and thinking levels
- [`docs/production-notes.md`](docs/production-notes.md) — limits and rollout checklist

## Related repositories

- [Gemini-4-Carbon-API](https://github.com/PoyoAPI/Gemini-4-Carbon-API) — Gemini 4 Carbon examples
- [GPT-6.2-API](https://github.com/PoyoAPI/GPT-6.2-API) — GPT-6.2 Astra and Sol through Chat Completions and Responses
- [awesome-poyo-api](https://github.com/PoyoAPI/awesome-poyo-api) — every PoYo model repository in one list
- [poyo-devtools](https://github.com/PoyoAPI/poyo-devtools) — PoYo CLI, MCP bridge, and Agent Skill

## Links

- [Gemini 4 Neon API on PoYo](https://poyo.ai/models/gemini-4-neon?utm_source=github&utm_medium=social&utm_campaign=gemini-4-neon-launch)
- [Gemini Native API reference](https://docs.poyo.ai/api-manual/chat-series/gemini-native-format?utm_source=github&utm_medium=social&utm_campaign=gemini-4-neon-launch)
- [Google models on PoYo](https://docs.poyo.ai/api-manual/chat-series/google?utm_source=github&utm_medium=social&utm_campaign=gemini-4-neon-launch)
- [Chat Completions API reference](https://docs.poyo.ai/api-manual/chat-series/chat-completions?utm_source=github&utm_medium=social&utm_campaign=gemini-4-neon-launch)
- [PoYo model catalog](https://poyo.ai/models?utm_source=github&utm_medium=social&utm_campaign=gemini-4-neon-launch)

## License

MIT
