# llm_client.py — LLM client

## Public APIs

- **`chat(host, model, messages, *, temperature=None, timeout=180.0)`** → `{"response": str, "done": bool, "usage": {...}}` — non-streaming.
- **`chat_stream(host, model, messages, *, temperature=None, timeout=180.0, stream_stats=None)`** → `AsyncIterator[str]` — streaming tokens. Accepts optional `stream_stats` dict for collecting eval counts.

## Helpers

- `_get_client(base_url)` → `AsyncOpenAI` — lazy singleton client creation.
- `apply_thinking(msgs, enable)` → `list[dict]` — appends `/think` or `/no_think` tag to last message.
- `strip_thinking(text)` → `str` — removes `<think>...</think>` tags via regex.
- `trim_messages(msgs, max_tokens)` → `tuple[list[dict], bool, int]` — token-budget trim; returns `(messages, was_truncated, chars_removed)`. Drops/truncates oldest non-system messages.
- `_mock_extract_chat(messages)` → `dict` — mock LLM response for tests (narrate/examine/cargo variants).
- `_mock_stream` — async iterator class for mock streaming.

## Constants

- `_MOCK_MODE` — `True` when `MOCK_MODE` env var is `"true"`, `"1"`, or `"yes"`.
- `_THINK_RE` — compiled regex `r"<think>.*?</think>"` for stripping thinking output.
- `_MOCK_NARRATE` — canned narrate response string.
- `_MOCK_EXTRACT_NARRATE`, `_MOCK_EXTRACT_EXAMINE`, `_MOCK_EXTRACT_CARGO` — canned extract responses for tests.
