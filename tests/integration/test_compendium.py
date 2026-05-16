"""Compendium dedup integration test.

Tests that compendium NPCs deduplicate by ID, name, and alias.
Uses the _dedup_compendium_add function directly (no LLM needed).
"""


from ccya.engine.extraction import _dedup_compendium_add
from ccya.models import CompendiumNpcUpdate


class TestCompendiumDedup:
    """Test compendium NPC deduplication by ID, name, and alias."""

    def test_dedup_redirects_name_match(self):
        """When the proposed NPC name matches an existing NPC name, redirect to the existing ID."""
        existing = [{"id": "torben_klask", "name": "Torben Klask", "aliases": ["the big man"]}]
        proposed = CompendiumNpcUpdate(id="the_big_man", name="Torben Klask")
        result = _dedup_compendium_add(proposed, existing)
        assert result.id == "torben_klask"

    def test_dedup_redirects_alias_match(self):
        """When the proposed NPC ID matches an existing NPC alias, redirect to the existing ID."""
        existing = [{"id": "kael_marsh", "name": "Kael Marsh", "aliases": ["the scarred soldier"]}]
        proposed = CompendiumNpcUpdate(id="scarred_soldier_new", name="Kael Marsh")
        result = _dedup_compendium_add(proposed, existing)
        assert result.id == "kael_marsh"

    def test_dedup_redirects_id_as_name(self):
        """When the proposed NPC ID matches an existing NPC name, redirect to the existing ID."""
        existing = [{"id": "halden", "name": "Halden", "aliases": []}]
        proposed = CompendiumNpcUpdate(id="new_halden", name="Halden")
        result = _dedup_compendium_add(proposed, existing)
        assert result.id == "halden"

    def test_dedup_allows_genuinely_new_npc(self):
        """When the proposed NPC is genuinely new (no name/alias match), allow it."""
        existing = [{"id": "torben_klask", "name": "Torben Klask", "aliases": []}]
        proposed = CompendiumNpcUpdate(id="sera_lant", name="Sera Lant")
        result = _dedup_compendium_add(proposed, existing)
        assert result.id == "sera_lant"

    def test_dedup_handles_empty_name(self):
        """When the proposed NPC has an empty name, allow it (no dedup possible)."""
        existing = [{"id": "torben_klask", "name": "Torben Klask", "aliases": []}]
        proposed = CompendiumNpcUpdate(id="mystery", name="")
        result = _dedup_compendium_add(proposed, existing)
        assert result.id == "mystery"

    def test_dedup_handles_case_insensitive(self):
        """Dedup should be case-insensitive for name matching."""
        existing = [{"id": "torben_klask", "name": "Torben Klask", "aliases": []}]
        proposed = CompendiumNpcUpdate(id="new_torben", name="torben klask")
        result = _dedup_compendium_add(proposed, existing)
        assert result.id == "torben_klask"

    def test_dedup_handles_empty_existing_list(self):
        """When the existing list is empty, the proposed NPC is always allowed."""
        proposed = CompendiumNpcUpdate(id="alice", name="Alice")
        result = _dedup_compendium_add(proposed, [])
        assert result.id == "alice"

    def test_dedup_handles_existing_with_aliases(self):
        """When an existing NPC has aliases, the proposed ID is checked against them."""
        existing = [
            {"id": "alice", "name": "Alice", "aliases": ["the baker", "alice smith"]},
            {"id": "bob", "name": "Bob", "aliases": ["the guard"]},
        ]
        proposed = CompendiumNpcUpdate(id="the_baker", name="Alice Smith")
        result = _dedup_compendium_add(proposed, existing)
        assert result.id == "alice"

    def test_dedup_allows_different_names(self):
        """When the proposed NPC name doesn't match any existing name, allow it."""
        existing = [
            {"id": "alice", "name": "Alice", "aliases": []},
            {"id": "bob", "name": "Bob", "aliases": []},
        ]
        proposed = CompendiumNpcUpdate(id="carol", name="Carol")
        result = _dedup_compendium_add(proposed, existing)
        assert result.id == "carol"

    def test_dedup_handles_unicode_names(self):
        """Dedup should handle Unicode characters in names."""
        existing = [{"id": "marie", "name": "Marie Dupont", "aliases": []}]
        proposed = CompendiumNpcUpdate(id="marie_dupont", name="Marie Dupont")
        result = _dedup_compendium_add(proposed, existing)
        assert result.id == "marie"

    def test_dedup_handles_spaces_in_id(self):
        """Dedup should handle IDs with spaces (normalized to underscores)."""
        existing = [{"id": "torben_klask", "name": "Torben Klask", "aliases": []}]
        proposed = CompendiumNpcUpdate(id="torben klask", name="Torben Klask")
        result = _dedup_compendium_add(proposed, existing)
        assert result.id == "torben_klask"
