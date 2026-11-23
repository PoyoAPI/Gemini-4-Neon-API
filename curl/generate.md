# Gemini 4 Neon API: cURL quickstart

```bash
export POYO_API_KEY="your-api-key"
export POYO_BASE_URL="https://api.poyo.ai"
```

Run these from the repository root so the `@payloads/...` paths resolve.

## Chat Completions (OpenAI format)

```bash
curl -X POST "$POYO_BASE_URL/v1/chat/completions" \
  -H "Authorization: Bearer $POYO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
  "model": "gemini-4-neon",
  "messages": [
    {
      "role": "system",
      "content": "You are a senior backend engineer. Be precise and explain each change."
    },
    {
      "role": "user",
      "content": "Write a Python function that validates an ISO 8601 date string without third-party libraries, with tests."
    }
  ],
  "max_tokens": 2048
}'
```

The full request body is in [`payloads/chat-completions.json`](../payloads/chat-completions.json):

```bash
curl -X POST "$POYO_BASE_URL/v1/chat/completions" \
  -H "Authorization: Bearer $POYO_API_KEY" \
  -H "Content-Type: application/json" \
  -d @payloads/chat-completions.json
```

## Streaming with Chat Completions

Add `"stream": true` to receive server-sent events. Each `data:` line carries a chunk with `choices[].delta.content`, and the stream ends with `data: [DONE]`.

```bash
curl -N -X POST "$POYO_BASE_URL/v1/chat/completions" \
  -H "Authorization: Bearer $POYO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
  "model": "gemini-4-neon",
  "messages": [
    {
      "role": "user",
      "content": "Explain the difference between optimistic and pessimistic locking in three sentences."
    }
  ],
  "stream": true
}'
```

## Gemini Native generateContent

The model ID goes in the URL path, not the body. The response is Google's `GenerateContentResponse` without a `code` / `data` wrapper.

```bash
curl -X POST "$POYO_BASE_URL/v1beta/models/gemini-4-neon:generateContent" \
  -H "Authorization: Bearer $POYO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
  "contents": [
    {
      "role": "user",
      "parts": [
        {
          "text": "Plan a step-by-step migration of a 200-file JavaScript codebase to TypeScript. List the phases, the risks in each phase, and how to verify each phase before moving on."
        }
      ]
    }
  ],
  "generationConfig": {
    "maxOutputTokens": 4096,
    "temperature": 0.7
  }
}'
```

## Gemini Native with a thinking level

Gemini 4 Neon has four thinking levels: `low`, `medium`, `high` (default), and `xhigh`. In the Gemini Native format the level goes in Google's `generationConfig.thinkingConfig.thinkingLevel` field. Omit it to use `high`.

```bash
curl -X POST "$POYO_BASE_URL/v1beta/models/gemini-4-neon:generateContent" \
  -H "Authorization: Bearer $POYO_API_KEY" \
  -H "Content-Type: application/json" \
  -d @payloads/gemini-native-thinking.json
```

Thinking tokens are billed as output tokens and reported in `usageMetadata.thoughtsTokenCount`.

## Gemini Native streaming

`streamGenerateContent` returns `text/event-stream`: each `data:` line is a partial `GenerateContentResponse`, and the stream ends with `data: [DONE]`. Concatenate the `text` parts in order and skip parts marked `thought: true` or carrying only a `thoughtSignature`.

```bash
curl -N -X POST "$POYO_BASE_URL/v1beta/models/gemini-4-neon:streamGenerateContent" \
  -H "Authorization: Bearer $POYO_API_KEY" \
  -H "Content-Type: application/json" \
  -d @payloads/gemini-native.json
```

Keep the API key on your server. Add timeouts, bounded retries, and usage logging before production.

See the [full README](../README.md) and [production notes](../docs/production-notes.md).
