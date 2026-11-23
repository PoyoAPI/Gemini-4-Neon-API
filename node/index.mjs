import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

for (const envPath of [resolve(process.cwd(), ".env"), resolve(process.cwd(), "../.env")]) {
  if (!existsSync(envPath)) continue;
  for (const line of readFileSync(envPath, "utf8").split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const index = trimmed.indexOf("=");
    if (index < 0) continue;
    const key = trimmed.slice(0, index).trim();
    const value = trimmed.slice(index + 1).trim();
    if (!process.env[key]) process.env[key] = value;
  }
}

const apiKey = process.env.POYO_API_KEY;
const baseUrl = (process.env.POYO_BASE_URL || "https://api.poyo.ai").replace(/\/+$/, "");
if (!apiKey || apiKey === "YOUR_POYO_API_KEY_HERE") {
  console.error("Set POYO_API_KEY in your environment or repo-root .env file.");
  process.exit(1);
}

const MODEL = "gemini-4-neon";

async function post(path, payload) {
  const response = await fetch(`${baseUrl}${path}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${apiKey}`, "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) await fail(response.status, await response.text());
  return response;
}

async function fail(status, text) {
  let body = {};
  if (text) {
    try { body = JSON.parse(text); } catch { body = { raw: text }; }
  }
  throw new Error(`PoYo request failed: ${JSON.stringify({ http_status: status, body }, null, 2)}`);
}

async function requestJson(path, payload) {
  const response = await post(path, payload);
  const text = await response.text();
  let body = {};
  if (text) {
    try { body = JSON.parse(text); } catch { body = { raw: text }; }
  }
  if (body?.error) await fail(response.status, text);
  return body;
}

// Yields each JSON event from a text/event-stream response until `data: [DONE]`.
async function* streamEvents(path, payload) {
  const response = await post(path, payload);
  const decoder = new TextDecoder();
  let buffer = "";
  for await (const chunk of response.body) {
    buffer += decoder.decode(chunk, { stream: true });
    const lines = buffer.split(/\r?\n/);
    buffer = lines.pop();
    for (const line of lines) {
      if (!line.startsWith("data:")) continue;
      const data = line.slice(5).trim();
      if (data === "[DONE]") return;
      const event = JSON.parse(data);
      if (event?.error) await fail(response.status, data);
      yield event;
    }
  }
}

// Thinking models can return parts without text (thought / thoughtSignature); keep only answer text.
function geminiText(event) {
  const parts = event.candidates?.[0]?.content?.parts ?? [];
  return parts.filter((part) => typeof part.text === "string" && !part.thought).map((part) => part.text).join("");
}

// Pass a payload file, e.g. `node node/index.mjs payloads/gemini-native.json`.
// Payloads with "contents" use Gemini Native; payloads with "messages" use Chat Completions.
// Add --stream to a Gemini Native payload to call streamGenerateContent.
const args = process.argv.slice(2).filter((arg) => !arg.startsWith("--"));
const nativeStream = process.argv.includes("--stream");
const repoRoot = fileURLToPath(new URL("..", import.meta.url));
const payloadPath = args[0]
  ? resolve(process.cwd(), args[0])
  : resolve(repoRoot, "payloads/chat-completions.json");
const payload = JSON.parse(readFileSync(payloadPath, "utf8"));

if (payload.contents) {
  if (nativeStream) {
    let usage;
    for await (const event of streamEvents(`/v1beta/models/${MODEL}:streamGenerateContent`, payload)) {
      process.stdout.write(geminiText(event));
      usage = event.usageMetadata ?? usage;
    }
    console.log();
    console.log(JSON.stringify({ usageMetadata: usage }, null, 2));
  } else {
    const result = await requestJson(`/v1beta/models/${MODEL}:generateContent`, payload);
    console.log(geminiText(result));
    console.log(JSON.stringify({ usageMetadata: result.usageMetadata }, null, 2));
  }
} else {
  const body = { ...payload, model: payload.model || MODEL };
  if (body.stream) {
    let usage;
    for await (const chunk of streamEvents("/v1/chat/completions", body)) {
      for (const choice of chunk.choices ?? []) process.stdout.write(choice.delta?.content ?? "");
      usage = chunk.usage ?? usage;
    }
    console.log();
    console.log(JSON.stringify({ usage }, null, 2));
  } else {
    const result = await requestJson("/v1/chat/completions", body);
    console.log(result.choices?.[0]?.message?.content ?? "");
    console.log(JSON.stringify({ usage: result.usage }, null, 2));
  }
}
