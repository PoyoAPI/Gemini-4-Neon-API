# Gemini 4 Neon API production notes

## Confirmed contract

- Chat Completions: `POST /v1/chat/completions` with `"model": "gemini-4-neon"`
- Gemini Native: `POST /v1beta/models/gemini-4-neon:generateContent` or `:streamGenerateContent`
- Authentication: `Authorization: Bearer <POYO_API_KEY>`
- Responses use each format's native shape, without the `code` / `data` wrapper used by generation tasks

## Input limits

| Field | Requirement | Constraint |
| --- | --- | --- |
| model (Chat Completions) | required | gemini-4-neon. |
| messages | required | Role/content messages: system, user, assistant. |
| max_tokens | optional | Integer ≥ 1. Gemini 4 Neon returns up to 64K output tokens per synchronous response by default. |
| temperature / top_p | optional | 0–2 / 0–1. |
| stream | optional | true returns server-sent events. |
| contents (Gemini Native) | required | Role (user or model) plus parts with text or inlineData. |
| generationConfig | optional | temperature (0–2), topP (0–1), topK (≥ 1), maxOutputTokens (≥ 1), stopSequences. |
| generationConfig.thinkingConfig.thinkingLevel | optional | Google's thinking control: low, medium, high (default), or xhigh. |
| safetySettings | optional | Category and threshold pairs. |

Context window: 1,048,576 tokens, shared by input, thinking, and output. Input: text, image, audio, video, and PDF; output: text.

Gemini Native errors use the Google error shape: `{"error": {"code": 400, "message": "...", "status": "INVALID_ARGUMENT"}}`. An unknown model id returns 404.

## Choosing a thinking level

| Level | Use it for |
| --- | --- |
| `low` / `medium` | Interactive coding, UI prototyping, and other latency-sensitive calls |
| `high` (default) | General tool-calling agents and everyday reasoning |
| `xhigh` | Hard architecture, math, science, and multi-step research |

Higher levels spend more thinking tokens, which are billed as output. Watch `usageMetadata.thoughtsTokenCount` when you raise the level.

## Operational checklist

- Keep API keys in a server-side secret manager.
- Validate user input before calling the API.
- Apply request timeouts long enough for `xhigh` thinking, and retry only rate limits or transient 5xx responses.
- Bound output tokens and log usage for cost control.
- Redact sensitive prompt and response content from logs.
- Recheck the live model page before hard-coding prices.

## Failure handling

Treat non-2xx HTTP responses and bodies with an `error` object as errors. Preserve the HTTP status and a redacted response body for debugging. Retry only 429 and transient 5xx responses.

Schema: [PoYo API documentation](https://docs.poyo.ai/api-manual/chat-series/gemini-native-format?utm_source=github&utm_medium=social&utm_campaign=gemini-4-neon-launch)
