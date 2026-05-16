"""Unit tests for architecture_context — file read tests."""

from ccya.eval import architecture_context


class TestLoadArchitectureContext:
    def test_returns_nonempty(self):
        result = architecture_context.load_architecture_context()
        assert result != ""
        assert "ENGINE DESIGN REFERENCE" in result

    def test_missing_markers(self, tmp_path):
        arch = tmp_path / "ARCHITECTURE.md"
        arch.write_text("# No markers here\n")
        original = architecture_context._ARCH_PATH
        try:
            architecture_context._ARCH_PATH = arch
            result = architecture_context.load_architecture_context()
            assert result == ""
        finally:
            architecture_context._ARCH_PATH = original
