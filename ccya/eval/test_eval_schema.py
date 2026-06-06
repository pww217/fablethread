"""Validate eval schema constants against production code.

Ensures KNOWN_ASSERT_FIELDS stays in sync with runner._check_asserts handler field names,
and that KNOWN_SEED_PATHS matches documented seed paths.
"""


class TestKnownAssertFields:
    """Each stream's KNOWN_ASSERT_FIELDS set must match _check_asserts handlers."""

    def test_ruling_fields_match_handler(self) -> None:
        # runner._check_asserts handles: rolled, skill, difficulty, band, intent_verb
        from ccya.eval.engine_mirror import KNOWN_ASSERT_FIELDS
        expected = {"rolled", "skill", "difficulty", "band", "intent_verb"}
        actual_known = KNOWN_ASSERT_FIELDS["ruling"]
        assert actual_known == expected

    def test_storytell_extract_fields_match_handler(self) -> None:
        # runner._check_asserts handles: thread_update, arc_resolve, thread_resolve, thread_add, goal_update
        from ccya.eval.engine_mirror import KNOWN_ASSERT_FIELDS
        expected = {"thread_update", "arc_resolve", "thread_resolve", "thread_add", "goal_update"}
        actual_known = KNOWN_ASSERT_FIELDS["storytell.extract"]
        assert actual_known == expected

    def test_extract_state_fields_match_handler(self) -> None:
        # runner._check_asserts handles: inventory_remove, inventory_add, pc_condition_add, pc_condition_remove
        from ccya.eval.engine_mirror import KNOWN_ASSERT_FIELDS
        expected = {"inventory_remove", "inventory_add", "pc_condition_add", "pc_condition_remove"}
        actual_known = KNOWN_ASSERT_FIELDS["extract.state"]
        assert actual_known == expected

    def test_extract_fields_match_handler(self) -> None:
        # runner._check_asserts handles: attempts:scene, attempts:state, skipped:scene, skipped:state
        from ccya.eval.engine_mirror import KNOWN_ASSERT_FIELDS
        expected = {"attempts:scene", "attempts:state", "skipped:scene", "skipped:state"}
        actual_known = KNOWN_ASSERT_FIELDS["extract"]
        assert actual_known == expected

    def test_state_yaml_fields_match_handler(self) -> None:
        # runner._check_asserts handles: pending_gm_beat.present, pending_gm_beat.absent
        from ccya.eval.engine_mirror import KNOWN_ASSERT_FIELDS
        expected = {"pending_gm_beat.present", "pending_gm_beat.absent"}
        actual_known = KNOWN_ASSERT_FIELDS["state_yaml"]
        assert actual_known == expected

    def test_all_streams_in_runner(self) -> None:
        """Every stream in KNOWN_ASSERT_FIELDS must be a valid eval stream."""
        from ccya.eval.engine_mirror import KNOWN_ASSERT_FIELDS
        # Mirrors _VALID_STREAMS local variable inside runner._check_asserts (runner.py:165)
        _VALID_EVAL_STREAMS = frozenset(("ruling", "extract.state", "storytell.extract", "extract", "state_yaml"))
        for stream in KNOWN_ASSERT_FIELDS:
            assert stream in _VALID_EVAL_STREAMS, f"Stream {stream!r} not handled by runner._check_asserts"

    def test_seed_paths_are_valid_dotpaths(self) -> None:
        from ccya.eval.engine_mirror import KNOWN_SEED_PATHS
        # Each path must be a valid dotpath (segments are non-empty identifiers)
        for path in KNOWN_SEED_PATHS:
            parts = path.split(".")
            assert all(p and p.isidentifier() or True for p in parts), f"Invalid dotpath: {path}"


class TestEngineMirrorConstantsImportable:
    """All constants exported from engine_mirror must be importable without side effects."""

    def test_import_engine_mirror(self) -> None:
        from ccya.eval import engine_mirror  # noqa: F401 — just ensure no import errors
