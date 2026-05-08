"""Unit tests for _split_scope_tail and _StreamTailFilter."""
from __future__ import annotations

from ccya.engine.turn import (
    _StreamTailFilter,
    _split_scope_tail,
)


class TestSplitScopeTail:
    def test_no_tag_returns_none(self) -> None:
        text = "Just prose, nothing special."
        prose, domains = _split_scope_tail(text)
        assert prose == text
        assert domains is None

    def test_valid_tag_at_end(self) -> None:
        text = 'The guard falls.\n\n<scope>{"active_domains":["scene","inventory"]}</scope>'
        prose, domains = _split_scope_tail(text)
        assert prose == "The guard falls."
        assert domains == ["scene", "inventory"]

    def test_empty_domain_list_honored(self) -> None:
        text = 'Pure dialogue beat.\n<scope>{"active_domains":[]}</scope>'
        prose, domains = _split_scope_tail(text)
        assert prose == "Pure dialogue beat."
        assert domains == []

    def test_unknown_domains_filtered(self) -> None:
        text = '...\n<scope>{"active_domains":["scene","fake_domain","inventory"]}</scope>'
        prose, domains = _split_scope_tail(text)
        assert domains == ["scene", "inventory"]

    def test_invalid_json_returns_none(self) -> None:
        text = '...<scope>{not json}</scope>'
        prose, domains = _split_scope_tail(text)
        assert prose == "..."
        assert domains is None

    def test_missing_active_domains_key(self) -> None:
        text = '...<scope>{"other":1}</scope>'
        _, domains = _split_scope_tail(text)
        assert domains is None

    def test_active_domains_not_list(self) -> None:
        text = '...<scope>{"active_domains":"scene"}</scope>'
        _, domains = _split_scope_tail(text)
        assert domains is None

    def test_tag_in_middle_of_text(self) -> None:
        # Defensive: even if the tag isn't at the end, parser should still find it.
        text = 'before <scope>{"active_domains":["scene"]}</scope> after'
        prose, domains = _split_scope_tail(text)
        assert "<scope>" not in prose
        assert "</scope>" not in prose
        assert domains == ["scene"]


class TestStreamTailFilter:
    def test_no_sentinel_passthrough(self) -> None:
        f = _StreamTailFilter()
        out: list[str] = []
        for chunk in ["hello ", "world", " end"]:
            out.append(f.feed(chunk))
        out.append(f.flush())
        assert "".join(out) == "hello world end"
        assert f.full_text() == "hello world end"

    def test_sentinel_in_single_chunk(self) -> None:
        f = _StreamTailFilter()
        emitted = f.feed('prose here.<scope>{"active_domains":["scene"]}</scope>')
        emitted += f.flush()
        assert emitted == "prose here."
        assert "<scope>" in f.full_text()

    def test_sentinel_split_across_chunks(self) -> None:
        f = _StreamTailFilter()
        emitted = ""
        for chunk in ["pro", "se ", "her", "e.<sc", "ope>", '{"active_domains":[]}', "</scope>"]:
            emitted += f.feed(chunk)
        emitted += f.flush()
        assert emitted == "prose here."
        assert f.full_text() == 'prose here.<scope>{"active_domains":[]}</scope>'

    def test_sentinel_split_at_every_char(self) -> None:
        # Worst-case: each char in its own chunk.
        text = 'abc.<scope>{"active_domains":["scene"]}</scope>'
        f = _StreamTailFilter()
        emitted = "".join(f.feed(c) for c in text)
        emitted += f.flush()
        assert emitted == "abc."

    def test_partial_buffer_flushed_at_end(self) -> None:
        # Stream ends mid-tail-buffer with no sentinel — must flush remainder.
        f = _StreamTailFilter()
        emitted = f.feed("ab")
        emitted += f.feed("c")
        emitted += f.flush()
        assert emitted == "abc"

    def test_no_emission_after_sentinel(self) -> None:
        f = _StreamTailFilter()
        f.feed("intro.<scope>")
        # Anything fed after sentinel must produce empty visible output.
        assert f.feed('{"active_domains":[]}') == ""
        assert f.feed("</scope>") == ""
        assert f.flush() == ""
