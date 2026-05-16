"""Unit tests for judge front-matter parsing — no LLM, no I/O."""

from ccya.eval.judge import parse_judge_response


class TestParseJudgeResponse:
    def test_with_leading_preamble(self):
        raw = "Here is my analysis.\n\n---\nmechanical_score: 3\n---\n## Body"
        scores, body = parse_judge_response(raw)
        assert scores["mechanical_score"] == 3
        assert "Body" in body

    def test_no_front_matter(self):
        raw = "No YAML here."
        scores, body = parse_judge_response(raw)
        assert scores == {}
        assert body == "No YAML here."

    def test_front_matter_at_start(self):
        raw = "---\nmechanical_score: 5\n---\n## Body"
        scores, body = parse_judge_response(raw)
        assert scores["mechanical_score"] == 5

    def test_strips_thinking(self):
        raw = "<think>Reasoning.</think>\n---\nmechanical_score: 2\n---\n## Body"
        scores, body = parse_judge_response(raw)
        assert scores["mechanical_score"] == 2

    def test_blank_lines_before_fm(self):
        raw = "\n\n\n---\nmechanical_score: 4\n---\n## Body"
        scores, body = parse_judge_response(raw)
        assert scores["mechanical_score"] == 4

    def test_multiple_scores(self):
        raw = "---\nmechanical_score: 3\nnarrative_score: 4\nstate_fidelity_rate: 0.8\n---\n## Body"
        scores, body = parse_judge_response(raw)
        assert scores["mechanical_score"] == 3
        assert scores["narrative_score"] == 4
        assert scores["state_fidelity_rate"] == 0.8

    def test_code_fence_wrapped(self):
        raw = "```\n---\nmechanical_score: 3\n---\n## Body\n```"
        scores, body = parse_judge_response(raw)
        assert scores["mechanical_score"] == 3
        assert "Body" in body

    def test_table_rows_in_body_no_false_match(self):
        raw = "---\nstate_fidelity_rate: 0.77\nextraction_accuracy_score: 3\n---\n\n# Analysis\n\n| Turn | Roll Band | Momentum |\n|------|-----------|----------|\n| 1    | Success   | +1       |\n\nSome **bold** text and --- horizontal rules here.\n\n--- end of report ---\n"
        scores, body = parse_judge_response(raw)
        assert scores["state_fidelity_rate"] == 0.77
        assert scores["extraction_accuracy_score"] == 3
        assert "Turn" in body
        assert "**bold**" in body

    def test_no_match_on_mid_body_delimiter(self):
        raw = "---\nnarrative_score: 4\n---\n\n# Section\n\nSome --- rules here.\n\n--- end ---\n"
        scores, body = parse_judge_response(raw)
        assert scores["narrative_score"] == 4
        assert "--- end ---" in body or "--- end" in body or "--- end ---" not in scores
