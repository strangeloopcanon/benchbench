from pathlib import Path
import subprocess
import tempfile
import time
import unittest

import benchbench_model_backends as backends
from benchbench_model_backends import (
    antigravity_model_id_from_label,
    antigravity_model_setting,
    claude_cache_summary,
    claude_tokens_used,
    parse_antigravity_selected_label,
    parse_model_spec,
    run_cmd,
    safe_name,
)
from benchbench_results import extract_predictions, extract_solver_predictions, score_summary
from run_broad_three_model_sweep import candidate_card_lines, candidate_status
from scripts.build_benchmark_landscape_pack import model_from_safe_slug, solver_model_from_score_path


class ModelBackendTests(unittest.TestCase):
    def test_codex_model_specs_are_default(self) -> None:
        spec = parse_model_spec("gpt-5.5")
        self.assertEqual(spec.provider, "codex")
        self.assertEqual(spec.codex_model, "gpt-5.5")
        self.assertEqual(spec.agent_label, "gpt-5.5+Codex")

    def test_antigravity_known_model_spec(self) -> None:
        spec = parse_model_spec("agy:gemini-3.5-flash-high")
        self.assertEqual(spec.provider, "antigravity")
        self.assertEqual(spec.name, "gemini-3.5-flash-high")
        self.assertEqual(spec.antigravity_expected_label, "Gemini 3.5 Flash (High)")
        self.assertEqual(spec.agent_label, "Gemini 3.5 Flash (High)+Antigravity")

    def test_antigravity_pro_alias_uses_high_label(self) -> None:
        spec = parse_model_spec("agy:gemini-3.1-pro")
        self.assertEqual(spec.provider, "antigravity")
        self.assertEqual(spec.name, "gemini-3.1-pro")
        self.assertEqual(spec.antigravity_expected_label, "Gemini 3.1 Pro (High)")
        self.assertEqual(spec.agent_label, "Gemini 3.1 Pro (High)+Antigravity")

    def test_antigravity_claude_model_spec(self) -> None:
        spec = parse_model_spec("agy:claude-sonnet-4.6-thinking")
        self.assertEqual(spec.provider, "antigravity")
        self.assertEqual(spec.name, "claude-sonnet-4.6-thinking")
        self.assertEqual(spec.antigravity_expected_label, "Claude Sonnet 4.6 (Thinking)")
        self.assertEqual(spec.agent_label, "Claude Sonnet 4.6 (Thinking)+Antigravity")

    def test_claude_model_spec(self) -> None:
        spec = parse_model_spec("claude:sonnet")
        self.assertEqual(spec.provider, "claude")
        self.assertEqual(spec.name, "sonnet")
        self.assertEqual(spec.claude_model, "sonnet")
        self.assertEqual(spec.agent_label, "Claude Sonnet+Claude Code")

    def test_claude_usage_parser_counts_cache_tokens(self) -> None:
        data = {
            "usage": {
                "input_tokens": 3,
                "cache_creation_input_tokens": 5,
                "cache_read_input_tokens": 7,
                "output_tokens": 11,
            }
        }
        self.assertEqual(claude_tokens_used(data), 26)
        self.assertEqual(
            claude_cache_summary(data),
            {"cache_creation_input_tokens": 5, "cache_read_input_tokens": 7},
        )

        with_model_usage = {
            "usage": {
                "input_tokens": 0,
                "cache_creation_input_tokens": 0,
                "cache_read_input_tokens": 0,
                "output_tokens": 0,
            },
            "modelUsage": {
                "claude-sonnet": {
                    "inputTokens": 13,
                    "cacheCreationInputTokens": 17,
                    "cacheReadInputTokens": 19,
                    "outputTokens": 23,
                }
            },
        }
        self.assertEqual(claude_tokens_used(with_model_usage), 72)
        self.assertEqual(
            claude_cache_summary(with_model_usage),
            {"cache_creation_input_tokens": 17, "cache_read_input_tokens": 19},
        )

    def test_antigravity_label_parser_uses_last_label(self) -> None:
        text = '\n'.join(
            [
                'model_config_manager.go:157] Propagating selected model override to backend: label="Gemini 3.1 Pro (High)"',
                'model_config_manager.go:157] Propagating selected model override to backend: label="Gemini 3.5 Flash (High)"',
            ]
        )
        self.assertEqual(parse_antigravity_selected_label(text), "Gemini 3.5 Flash (High)")
        self.assertEqual(antigravity_model_id_from_label("Gemini 3.5 Flash (High)"), "gemini-3.5-flash-high")
        self.assertEqual(antigravity_model_id_from_label("Gemini 3.1 Pro (High)"), "gemini-3.1-pro")

    def test_antigravity_model_setting_restores_original_file(self) -> None:
        original_settings_path = backends.ANTIGRAVITY_SETTINGS_PATH
        original_lock_path = backends.ANTIGRAVITY_SETTINGS_LOCK_PATH
        with tempfile.TemporaryDirectory(prefix="benchbench-agy-settings-test.") as tmp:
            tmp_path = Path(tmp)
            backends.ANTIGRAVITY_SETTINGS_PATH = tmp_path / "settings.json"
            backends.ANTIGRAVITY_SETTINGS_LOCK_PATH = tmp_path / "settings.lock"
            try:
                backends.ANTIGRAVITY_SETTINGS_PATH.write_text(
                    '{"model":"Gemini 3.5 Flash (High)","x":1}\n',
                    encoding="utf-8",
                )
                with antigravity_model_setting("Gemini 3.1 Pro (High)"):
                    text = backends.ANTIGRAVITY_SETTINGS_PATH.read_text(encoding="utf-8")
                    self.assertIn('"model": "Gemini 3.1 Pro (High)"', text)
                self.assertEqual(
                    backends.ANTIGRAVITY_SETTINGS_PATH.read_text(encoding="utf-8"),
                    '{"model":"Gemini 3.5 Flash (High)","x":1}\n',
                )
            finally:
                backends.ANTIGRAVITY_SETTINGS_PATH = original_settings_path
                backends.ANTIGRAVITY_SETTINGS_LOCK_PATH = original_lock_path

    def test_run_cmd_timeout_kills_child_process_group(self) -> None:
        with tempfile.TemporaryDirectory(prefix="benchbench-timeout-test.") as tmp:
            tmp_path = Path(tmp)
            child = tmp_path / "child_timeout_marker.py"
            parent = tmp_path / "parent_timeout_marker.py"
            child.write_text("import time\ntime.sleep(60)\n", encoding="utf-8")
            parent.write_text(
                "import subprocess, sys, time\n"
                f"subprocess.Popen([sys.executable, {str(child)!r}])\n"
                "time.sleep(60)\n",
                encoding="utf-8",
            )
            with self.assertRaises(subprocess.TimeoutExpired):
                run_cmd(["python", str(parent)], tmp_path, timeout=1)
            time.sleep(0.2)
            ps = subprocess.run(["ps", "-axo", "command"], text=True, capture_output=True, check=False)
            self.assertNotIn(str(child), ps.stdout)

    def test_safe_names_and_landscape_model_parsing(self) -> None:
        self.assertEqual(safe_name("Gemini 3.5 Flash (High)"), "gemini_3_5_flash_high")
        self.assertEqual(model_from_safe_slug("gpt_5_5"), "gpt-5.5")
        self.assertEqual(model_from_safe_slug("gemini_3_5_flash_high"), "gemini-3.5-flash-high")
        solver, effort = solver_model_from_score_path(Path("score_solver_gemini_3_1_pro.json"))
        self.assertEqual((solver, effort), ("gemini-3.1-pro", "default"))

    def test_score_summary_accepts_creator_score_formats(self) -> None:
        with tempfile.TemporaryDirectory(prefix="benchbench-score-summary-test.") as tmp:
            tmp_path = Path(tmp)
            score_json = tmp_path / "score.json"
            score_json.write_text('{"score": 30, "total": 30}\n', encoding="utf-8")
            self.assertEqual(score_summary(score_json), {"total": 30, "correct": 30, "accuracy": 1.0})

            score_text = tmp_path / "score.txt"
            score_text.write_text("Score: 6/30\n", encoding="utf-8")
            self.assertEqual(score_summary(score_text), {"total": 30, "correct": 6, "accuracy": 0.2})

            score_exact = tmp_path / "score_exact.json"
            score_exact.write_text('{"total_gold": 30, "exact_match": 22, "accuracy": 0.7333333333333333}\n', encoding="utf-8")
            self.assertEqual(score_summary(score_exact), {"total": 30, "correct": 22, "accuracy": 0.7333333333333333})

            score_predictions = tmp_path / "score_predictions.json"
            score_predictions.write_text('{"total_items": 30, "correct_predictions": 11, "accuracy": 0.36666666666666664}\n', encoding="utf-8")
            self.assertEqual(score_summary(score_predictions), {"total": 30, "correct": 11, "accuracy": 0.36666666666666664})

            score_string = tmp_path / "score_string.json"
            score_string.write_text('{"total": 30, "score": "2/30"}\n', encoding="utf-8")
            self.assertEqual(score_summary(score_string), {"total": 30, "correct": 2, "accuracy": 2 / 30})

            score_details = tmp_path / "score_details.json"
            score_details.write_text(
                '{"accuracy": 0.5, "details": [{"correct": true}, {"correct": false}]}\n',
                encoding="utf-8",
            )
            self.assertEqual(score_summary(score_details), {"total": 2, "correct": 1, "accuracy": 0.5})

    def test_prediction_extraction_prefers_solver_written_file(self) -> None:
        with tempfile.TemporaryDirectory(prefix="benchbench-prediction-extract-test.") as tmp:
            tmp_path = Path(tmp)
            raw_out = tmp_path / "stdout.jsonl"
            solver_dir = tmp_path / "solver"
            solver_dir.mkdir()
            raw_out.write_text('{"id":"1","answer":"stdout"}\n', encoding="utf-8")
            (solver_dir / "predictions.jsonl").write_text(
                '{"id":1,"answer":"file-one"}\n{"id":"2","answer":"file-two"}\n',
                encoding="utf-8",
            )
            self.assertEqual(
                extract_predictions(raw_out.read_text(encoding="utf-8"), ["1", "2"]),
                [{"id": "1", "answer": "stdout"}],
            )
            predictions, source = extract_solver_predictions(raw_out, solver_dir, ["1", "2"])
            self.assertEqual(
                predictions,
                [{"id": "1", "answer": "file-one"}, {"id": "2", "answer": "file-two"}],
            )
            self.assertEqual(source, str(solver_dir / "predictions.jsonl"))

    def test_candidate_status_flags_all_zero_for_audit(self) -> None:
        self.assertEqual(candidate_status([{"total": 30, "correct": 0, "accuracy": 0.0}]), "solvability_audit")
        self.assertEqual(candidate_status([{"total": 30, "correct": 14, "accuracy": 14 / 30}]), "accept")
        self.assertEqual(candidate_status([{"total": 30, "correct": 15, "accuracy": 0.5}]), "reject")

    def test_candidate_card_summarizes_benchmark_mechanics(self) -> None:
        with tempfile.TemporaryDirectory(prefix="benchbench-card-test.") as tmp:
            tmp_path = Path(tmp)
            (tmp_path / "benchmark_spec.json").write_text(
                '{'
                '"name":"Card Test",'
                '"description":"Answer messy document questions.",'
                '"capability_claim":"Cross-document evidence use.",'
                '"grading_method":"Exact match.",'
                '"closest_existing_benchmarks":[{"name":"DocVQA","reason":"Document grounding."}]'
                '}\n',
                encoding="utf-8",
            )
            (tmp_path / "README.md").write_text("# Card Test\n\nFallback paragraph.\n", encoding="utf-8")
            (tmp_path / "failure_modes.md").write_text("# Failures\n\nObvious parser shortcut.\n", encoding="utf-8")
            (tmp_path / "score_solver_gpt_5_2.json").write_text('{"correct": 7, "total": 30}\n', encoding="utf-8")

            spec = parse_model_spec("gpt-5.2")
            lines = candidate_card_lines(
                spec,
                tmp_path,
                {"valid": True, "bundle_file_count": 3, "leak_matches": []},
            )
            text = "\n".join(lines)
            self.assertIn("What it asks: Answer messy document questions.", text)
            self.assertIn("Intended capability: Cross-document evidence use.", text)
            self.assertIn("Closest existing benchmarks: DocVQA", text)
            self.assertIn("Solver results: gpt-5.2: 7/30", text)


if __name__ == "__main__":
    unittest.main()
