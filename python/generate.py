"""Gemini 4 Neon API example for PoYo (Python 3.9+, standard library only).

Usage:
    python python/generate.py                                            # Chat Completions (OpenAI format)
    python python/generate.py payloads/chat-completions-stream.json      # Chat Completions, streaming
    python python/generate.py payloads/gemini-native.json                # Gemini Native generateContent
    python python/generate.py payloads/gemini-native-thinking.json       # Gemini Native, thinkingLevel xhigh
    python python/generate.py payloads/gemini-native.json --stream       # Gemini Native streamGenerateContent
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PAYLOAD = ROOT / "payloads" / "chat-completions.json"
MODEL = "gemini-4-neon"


def load_env() -> None:
    for env_path in (Path.cwd() / ".env", ROOT / ".env"):
        if not env_path.exists():
            continue
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


load_env()
API_KEY = os.environ.get("POYO_API_KEY", "")
BASE_URL = os.environ.get("POYO_BASE_URL", "https://api.poyo.ai").rstrip("/")
if not API_KEY or API_KEY == "YOUR_POYO_API_KEY_HERE":
    sys.exit("Set POYO_API_KEY in your environment or repo-root .env file.")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "User-Agent": "poyo-gemini-4-neon-api-example/1.0",
}


def fail(status: int, text: str) -> None:
    try:
        body = json.loads(text) if text else {}
    except ValueError:
        body = {"raw": text}
    raise RuntimeError(f"PoYo request failed: {json.dumps({'http_status': status, 'body': body}, indent=2)}")


def open_request(path: str, payload: dict):
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(f"{BASE_URL}{path}", data=data, headers=HEADERS, method="POST")
    try:
        return urllib.request.urlopen(request, timeout=600)
    except urllib.error.HTTPError as error:
        fail(error.code, error.read().decode("utf-8", "replace"))


def post_json(path: str, payload: dict) -> dict:
    with open_request(path, payload) as response:
        status, text = response.status, response.read().decode("utf-8")
    try:
        body = json.loads(text) if text else {}
    except ValueError:
        body = {"raw": text}
    if status >= 400 or (isinstance(body, dict) and body.get("error")):
        fail(status, text)
    return body


def stream_events(path: str, payload: dict):
    """Yield each JSON event from a text/event-stream response until `data: [DONE]`."""
    with open_request(path, payload) as response:
        for raw in response:
            line = raw.decode("utf-8").strip()
            if not line.startswith("data:"):
                continue
            data = line[len("data:"):].strip()
            if data == "[DONE]":
                return
            event = json.loads(data)
            if isinstance(event, dict) and event.get("error"):
                fail(response.status, data)
            yield event


def gemini_text(event: dict) -> str:
    candidates = event.get("candidates") or [{}]
    parts = (candidates[0].get("content") or {}).get("parts") or []
    # Thinking models can return parts without text (thought / thoughtSignature); keep only answer text.
    return "".join(p["text"] for p in parts if isinstance(p.get("text"), str) and not p.get("thought"))


args = [a for a in sys.argv[1:] if not a.startswith("--")]
native_stream = "--stream" in sys.argv[1:]
payload_path = Path(args[0]) if args else DEFAULT_PAYLOAD
payload = json.loads(payload_path.read_text(encoding="utf-8"))

if "contents" in payload:
    if native_stream:
        usage = None
        for event in stream_events(f"/v1beta/models/{MODEL}:streamGenerateContent", payload):
            print(gemini_text(event), end="", flush=True)
            usage = event.get("usageMetadata") or usage
        print()
        print(json.dumps({"usageMetadata": usage}, indent=2))
    else:
        result = post_json(f"/v1beta/models/{MODEL}:generateContent", payload)
        print(gemini_text(result))
        print(json.dumps({"usageMetadata": result.get("usageMetadata")}, indent=2))
else:
    payload.setdefault("model", MODEL)
    if payload.get("stream"):
        usage = None
        for chunk in stream_events("/v1/chat/completions", payload):
            for choice in chunk.get("choices") or []:
                print((choice.get("delta") or {}).get("content") or "", end="", flush=True)
            usage = chunk.get("usage") or usage
        print()
        print(json.dumps({"usage": usage}, indent=2))
    else:
        result = post_json("/v1/chat/completions", payload)
        choices = result.get("choices") or [{}]
        print((choices[0].get("message") or {}).get("content") or "")
        print(json.dumps({"usage": result.get("usage")}, indent=2))
