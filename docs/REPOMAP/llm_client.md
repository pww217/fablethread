# llm_client.py — LLM client

## Public APIs

- **`chat(host, model, messages, temperature, timeout)`** → `{"response": str, "usage": {...}}` — non-streaming.
- **`chat_stream(host, model, messages, temperature, timeout)`** → `AsyncIterator[str]` — streaming tokens.

## Helpers

- `apply_thinking(msgs, enable)` — wrap messages for thinking model
- `strip_thinking(text)` — remove thinking tags from output
- `trim_messages(msgs, max_tokens)` — token-budget trim; returns `(messages, was_truncated, chars_removed)`

## Mock mode

- `MOCK_MODE=true` env var returns canned responses (used in tests).
