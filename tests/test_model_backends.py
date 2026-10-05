from pathlib import Path
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch

import benchbench_model_backends as backends
from benchbench_model_backends import (
    antigravity_tokens_used,
    antigravity_model_id_from_label,
    claude_cache_summary,
    claude_tokens_used,
    codex_supported_efforts,
    cursor_tokens_used,
    effective_effort,
    parse_antigravity_selected_label,
    parse_model_spec,
    preflight_model,
    run_antigravity_model,
    run_claude_model,
    run_cmd,
    run_codex_model,
    run_cursor_model,
    safe_name,
)
from benchbench_results import extract_predictions, extract_solver_predictions, score_summary
from benchbench_run_state import call_artifact_id
from run_broad_three_model_sweep import (
    DEFAULT_MODELS,
    FRONTIER_FIVE_MODELS,
    FRONTIER_FOUR_MODELS,
    candidate_card_lines,
    candidate_status,
    resolve_model_lists,
    resolve_panel_policy,
)
from scripts.build_benchmark_landscape_pack import model_from_safe_slug, solver_model_from_score_path


class ModelBackendTests(unittest.TestCase):
    def test_codex_model_specs_are_default(self) -> None:
        spec = parse_model_spec("gpt-5.5")
        self.assertEqual(spec.provider, "codex")
        self.assertEqual(spec.codex_model, "gpt-5.5")
        self.assertEqual(spec.agent_label, "gpt-5.5+Codex")

    def test_panel_specs_preserve_per_model_effort(self) -> None:
        sol = parse_model_spec("gpt-5.6-sol@high")
        terra = parse_model_spec("gpt-5.6-terra@xhigh")
        self.assertEqual((sol.codex_model, effective_effort(sol, "low")), ("gpt-5.6-sol", "high"))
        self.assertEqual((terra.codex_model, effective_effort(terra, "low")), ("gpt-5.6-terra", "xhigh"))

        gemini = parse_model_spec("agy:gemini-3.6-flash-high@high")
        self.assertEqual(gemini.antigravity_model, "gemini-3.6-flash-high")
        self.assertEqual(gemini.antigravity_expected_label, "Gemini 3.6 Flash (High)")
        self.assertEqual(gemini.reasoning_effort, "high")

        gemini_37 = parse_model_spec("agy:gemini-3.7-flash-high@high")
        self.assertEqual(gemini_37.antigravity_model, "gemini-3.7-flash-high")
        self.assertEqual(gemini_37.antigravity_expected_label, "Gemini 3.7 Flash (High)")
        self.assertEqual(gemini_37.reasoning_effort, "high")

        halcyon = parse_model_spec("agy:halcyon@high")
        self.assertEqual(halcyon.antigravity_model, "halcyon")
        self.assertEqual(halcyon.antigravity_expected_label, "Halcyon")
        self.assertEqual(halcyon.reasoning_effort, "high")

        opus = parse_model_spec("cursor:claude-opus-5@high")
        self.assertEqual(opus.cursor_model, "claude-opus-5-thinking-high")
        self.assertEqual(opus.reasoning_effort, "high")

    def test_unknown_model_effort_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported reasoning effort"):
            parse_model_spec("gpt-5.6-sol@extreme")

    def test_codex_catalog_efforts_are_scoped_to_requested_model(self) -> None:
        catalog = (
            '{"models":['
            '{"slug":"gpt-5.6-sol","supported_reasoning_levels":[{"effort":"high"}]},'
            '{"slug":"gpt-5.6-terra","supported_reasoning_levels":[{"effort":"xhigh"}]}'
            ']}'
        )
        self.assertEqual(codex_supported_efforts(catalog, "gpt-5.6-sol"), {"high"})
        self.assertEqual(codex_supported_efforts(catalog, "gpt-5.6-terra"), {"xhigh"})
        self.assertIsNone(codex_supported_efforts(catalog, "missing"))

    def test_antigravity_known_model_spec(self) -> None:
        spec = parse_model_spec("agy:gemini-3.5-flash-high")
        self.assertEqual(spec.provider, "antigravity")
        self.assertEqual(spec.name, "gemini-3.5-flash-high")
        self.assertEqual(spec.antigravity_model, "gemini-3.5-flash-high")
        self.assertEqual(spec.antigravity_expected_label, "Gemini 3.5 Flash (High)")
        self.assertEqual(spec.agent_label, "Gemini 3.5 Flash (High)+Antigravity")

    def test_antigravity_pro_alias_uses_high_label(self) -> None:
        spec = parse_model_spec("agy:gemini-3.1-pro")
        self.assertEqual(spec.provider, "antigravity")
        self.assertEqual(spec.name, "gemini-3.1-pro")
        self.assertEqual(spec.antigravity_model, "gemini-3.1-pro-high")
        self.assertEqual(spec.antigravity_expected_label, "Gemini 3.1 Pro (High)")
        self.assertEqual(spec.agent_label, "Gemini 3.1 Pro (High)+Antigravity")

    def test_unknown_antigravity_model_is_passed_explicitly(self) -> None:
        spec = parse_model_spec("agy:typo-model")
        self.assertEqual(spec.antigravity_model, "typo-model")

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

    def test_cursor_model_spec(self) -> None:
        spec = parse_model_spec("cursor:claude-opus")
        self.assertEqual(spec.provider, "cursor")
        self.assertEqual(spec.name, "claude-opus")
        self.assertEqual(spec.cursor_model, "claude-4.6-opus-high-thinking")
        self.assertEqual(spec.agent_label, "Claude Opus 4.6 Thinking+Cursor")

    def test_cursor_fable_model_spec(self) -> None:
        spec = parse_model_spec("cursor:fable")
        self.assertEqual(spec.provider, "cursor")
        self.assertEqual(spec.name, "fable")
        self.assertEqual(spec.cursor_model, "claude-fable-5-thinking-high")
        self.assertEqual(spec.agent_label, "Claude Fable 5 Thinking+Cursor")

        xhigh = parse_model_spec("cursor:fable-xhigh")
        self.assertEqual(xhigh.cursor_model, "claude-fable-5-thinking-xhigh")

    def test_artifact_ids_are_provider_qualified(self) -> None:
        codex = parse_model_spec("gpt-5.2")
        cursor = parse_model_spec("cursor:gpt-5.2")
        self.assertEqual(codex.artifact_id, "codex__gpt_5_2")
        self.assertEqual(cursor.artifact_id, "cursor__gpt_5_2")
        self.assertNotEqual(codex.artifact_id, cursor.artifact_id)

    def test_aliases_collapse_to_the_same_concrete_provider_identity(self) -> None:
        opus_alias = parse_model_spec("cursor:opus-5")
        opus_named = parse_model_spec("cursor:claude-opus-5")
        opus_concrete = parse_model_spec("cursor:claude-opus-5-thinking-high")
        self.assertEqual(
            {opus_alias.artifact_id, opus_named.artifact_id, opus_concrete.artifact_id},
            {"cursor__claude_opus_5_thinking_high"},
        )

        flash_alias = parse_model_spec("agy:gemini-3.6-flash")
        flash_concrete = parse_model_spec("agy:gemini-3.6-flash-high")
        self.assertEqual(
            flash_alias.artifact_id,
            flash_concrete.artifact_id,
        )
        flash_37_alias = parse_model_spec("agy:gemini-3.7-flash")
        flash_37_concrete = parse_model_spec("agy:gemini-3.7-flash-high")
        self.assertEqual(flash_37_alias.artifact_id, flash_37_concrete.artifact_id)

        halcyon_alias = parse_model_spec("agy:halcyon")
        halcyon_concrete = parse_model_spec("agy:halcyon-high")
        self.assertEqual(halcyon_alias.artifact_id, "antigravity__halcyon")
        self.assertEqual(halcyon_alias.artifact_id, halcyon_concrete.artifact_id)

    def test_historical_xhigh_score_names_preserve_model_identity(self) -> None:
        for filename in ("score_solver_xhigh_gpt_5_5.json", "score_solver_gpt_5_5_xhigh.json"):
            model, effort = solver_model_from_score_path(Path(filename))
            self.assertEqual(model, "gpt-5.5")
            self.assertEqual(effort, "xhigh")

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

    def test_cursor_usage_parser_counts_cache_tokens(self) -> None:
        data = {
            "usage": {
                "inputTokens": 3,
                "cacheWriteTokens": 5,
                "cacheReadTokens": 7,
                "outputTokens": 11,
            }
        }
        self.assertEqual(cursor_tokens_used(data), 26)

    def test_antigravity_usage_parser_prefers_provider_total(self) -> None:
        data = {
            "usage": {
                "input_tokens": 19,
                "output_tokens": 5,
                "thinking_tokens": 3,
                "cache_read_tokens": 2,
                "total_tokens": 24,
            }
        }
        self.assertEqual(antigravity_tokens_used(data), 24)

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

    def test_codex_runtime_identity_is_verified_from_provider_banner(self) -> None:
        spec = parse_model_spec("gpt-5.6-sol@high")
        good = backends.codex_runtime_metadata(
            "model: gpt-5.6-sol\nreasoning effort: high\n",
            spec,
            "high",
        )
        self.assertFalse(good["model_mismatch"])
        self.assertEqual(good["runtime_model_reported"], "gpt-5.6-sol")
        self.assertTrue(
            backends.codex_runtime_metadata(
                "model: fallback\nreasoning effort: high\n",
                spec,
                "high",
            )["model_mismatch"]
        )
        self.assertTrue(backends.codex_runtime_metadata("", spec, "high")["model_mismatch"])

    def test_provider_commands_use_safe_modes_without_permission_bypass(self) -> None:
        completed = subprocess.CompletedProcess([], 0, '{"result":"ok","usage":{}}', "")
        with tempfile.TemporaryDirectory(prefix="benchbench-safe-backends-test.") as tmp:
            tmp_path = Path(tmp)
            with (
                patch.object(backends, "run_cmd", return_value=completed) as run,
                patch.object(
                    backends.shutil,
                    "which",
                    side_effect=lambda name: f"/usr/local/bin/{name}",
                ),
            ):
                run_codex_model(parse_model_spec("gpt-5.5"), "prompt", tmp_path / "codex.txt", tmp_path, "high", 5)
                codex_cmd = run.call_args.args[0]
                self.assertIn("danger-full-access", codex_cmd)
                self.assertIn("--ignore-user-config", codex_cmd)
                self.assertIn('model_provider="benchbench_chatgpt"', codex_cmd)
                self.assertIn(
                    'model_providers.benchbench_chatgpt.auth.command="/usr/bin/printenv"',
                    codex_cmd,
                )
                self.assertIn("shell_environment_policy.inherit=none", codex_cmd)
                self.assertIn(
                    'shell_environment_policy.exclude=["^BENCHBENCH_CODEX_BEARER_TOKEN$","^BENCHBENCH_CODEX_ACCOUNT_ID$"]',
                    codex_cmd,
                )
                self.assertNotIn("--dangerously-bypass-approvals-and-sandbox", codex_cmd)

                run_antigravity_model(parse_model_spec("agy:gemini-3.1-pro"), "prompt", tmp_path / "agy.txt", tmp_path, "high", 5)
                agy_cmd = run.call_args.args[0]
                self.assertIn("--model", agy_cmd)
                self.assertIn("gemini-3.1-pro-high", agy_cmd)
                self.assertEqual(agy_cmd[agy_cmd.index("--effort") + 1], "high")
                self.assertIn("--sandbox", agy_cmd)
                self.assertNotIn("--dangerously-skip-permissions", agy_cmd)

                run_antigravity_model(parse_model_spec("agy:halcyon"), "prompt", tmp_path / "agy_halcyon.txt", tmp_path, "high", 5)
                agy_halcyon_cmd = run.call_args.args[0]
                self.assertEqual(agy_halcyon_cmd[agy_halcyon_cmd.index("--model") + 1], "halcyon")
                self.assertNotIn("--effort", agy_halcyon_cmd)
                self.assertIn("--sandbox", agy_halcyon_cmd)

                run_claude_model(parse_model_spec("claude:sonnet"), "prompt", tmp_path / "claude.txt", tmp_path, "high", 5)
                claude_cmd = run.call_args.args[0]
                self.assertEqual(claude_cmd[claude_cmd.index("--permission-mode") + 1], "default")
                self.assertNotIn("bypassPermissions", claude_cmd)

                run_cursor_model(parse_model_spec("cursor:claude-opus-5"), "prompt", tmp_path / "cursor.txt", tmp_path, "high", 5)
                cursor_cmd = run.call_args.args[0]
                self.assertEqual(cursor_cmd[cursor_cmd.index("--model") + 1], "claude-opus-5-thinking-high")
                self.assertEqual(cursor_cmd[cursor_cmd.index("--sandbox") + 1], "enabled")
                self.assertNotIn("--force", cursor_cmd)
                self.assertIn("--trust", cursor_cmd)
                self.assertNotIn("--yolo", cursor_cmd)

    def test_antigravity_permission_denial_is_not_reported_as_success(self) -> None:
        completed = subprocess.CompletedProcess(
            [],
            0,
            '{"status":"CANCELED","response":"","usage":{"total_tokens":123}}',
            'jetski: no output produced — a tool required the "read_file" permission '
            "that headless mode cannot prompt for, so it was auto-denied.",
        )
        with tempfile.TemporaryDirectory(prefix="benchbench-agy-denial-test.") as tmp:
            tmp_path = Path(tmp)
            with (
                patch.object(backends, "run_cmd", return_value=completed),
                patch.object(backends.shutil, "which", return_value="/usr/local/bin/agy"),
            ):
                result = run_antigravity_model(
                    parse_model_spec("agy:gemini-3.1-pro"),
                    "prompt",
                    tmp_path / "agy.txt",
                    tmp_path,
                    "high",
                    5,
                )
        self.assertEqual(result["returncode"], 77)
        self.assertTrue(result["permission_denied"])
        self.assertEqual(result["tokens_used"], 123)

    def test_antigravity_print_timeout_is_not_reported_as_success(self) -> None:
        completed = subprocess.CompletedProcess(
            [],
            0,
            '{"status":"SUCCESS","response":"","usage":{"total_tokens":478796}}',
            "[agy] print timeout after 25m0s with turn in progress; returning partial output\n",
        )
        with tempfile.TemporaryDirectory(prefix="benchbench-agy-timeout-test.") as tmp:
            tmp_path = Path(tmp)
            with (
                patch.object(backends, "run_cmd", return_value=completed),
                patch.object(backends.shutil, "which", return_value="/usr/local/bin/agy"),
            ):
                result = run_antigravity_model(
                    parse_model_spec("agy:halcyon"),
                    "prompt",
                    tmp_path / "agy.txt",
                    tmp_path,
                    "high",
                    1500,
                )
        self.assertEqual(result["returncode"], -124)
        self.assertTrue(result["print_timeout"])
        self.assertEqual(result["tokens_used"], 478796)

    def test_antigravity_canceled_status_fails_even_without_permission_stderr(self) -> None:
        completed = subprocess.CompletedProcess(
            [],
            0,
            '{"status":"CANCELED","response":"partial","usage":{"total_tokens":7}}',
            "",
        )
        with tempfile.TemporaryDirectory(prefix="benchbench-agy-canceled-test.") as tmp:
            tmp_path = Path(tmp)
            with (
                patch.object(backends, "run_cmd", return_value=completed),
                patch.object(backends.shutil, "which", return_value="/usr/local/bin/agy"),
            ):
                result = run_antigravity_model(
                    parse_model_spec("agy:gemini-3.1-pro"),
                    "prompt",
                    tmp_path / "agy.txt",
                    tmp_path,
                    "high",
                    5,
                )
        self.assertEqual(result["returncode"], 78)
        self.assertEqual(result["antigravity_status"], "CANCELED")
        self.assertFalse(result["permission_denied"])

    def test_antigravity_missing_status_fails_closed(self) -> None:
        completed = subprocess.CompletedProcess([], 0, '{"response":"answer"}', "")
        with tempfile.TemporaryDirectory(prefix="benchbench-agy-status-test.") as tmp:
            tmp_path = Path(tmp)
            with (
                patch.object(backends, "run_cmd", return_value=completed),
                patch.object(backends.shutil, "which", return_value="/usr/local/bin/agy"),
            ):
                result = run_antigravity_model(
                    parse_model_spec("agy:gemini-3.1-pro"),
                    "prompt",
                    tmp_path / "agy.txt",
                    tmp_path,
                    "high",
                    5,
                )
        self.assertEqual(result["returncode"], 78)
        self.assertIsNone(result["antigravity_status"])

    def test_preflight_reports_missing_binary_without_inference(self) -> None:
        with tempfile.TemporaryDirectory(prefix="benchbench-preflight-test.") as tmp:
            with patch.object(backends.shutil, "which", return_value=None):
                result = preflight_model(parse_model_spec("cursor:fable"), Path(tmp))
        self.assertEqual(result["state"], "binary_missing")
        self.assertEqual(result["returncode"], 127)
        self.assertFalse(result["inference_attempted"])
        self.assertIsNone(result["model_available"])

    def test_preflight_lists_cursor_models_without_inference(self) -> None:
        with tempfile.TemporaryDirectory(prefix="benchbench-preflight-test.") as tmp:
            spec = parse_model_spec("cursor:fable")
            responses = [
                subprocess.CompletedProcess(["cursor-agent", "--help"], 0, "safe help", ""),
                subprocess.CompletedProcess(["cursor-agent", "--list-models"], 0, "claude-fable-5-thinking-high", ""),
            ]
            with (
                patch.object(backends.shutil, "which", return_value="/mock/cursor-agent"),
                patch.object(backends, "run_cmd", side_effect=responses) as run,
            ):
                result = preflight_model(spec, Path(tmp))
        self.assertEqual(result["state"], "binary_ready")
        self.assertTrue(result["model_listing_supported"])
        self.assertTrue(result["model_available"])
        self.assertFalse(result["inference_attempted"])
        self.assertEqual(run.call_args_list[0].args[0], ["/mock/cursor-agent", "--help"])
        self.assertEqual(run.call_args_list[1].args[0], ["/mock/cursor-agent", "--list-models"])

    def test_preflight_rejects_near_prefix_model_ids(self) -> None:
        with tempfile.TemporaryDirectory(prefix="benchbench-preflight-test.") as tmp:
            spec = parse_model_spec("cursor:claude-fable-5-thinking")
            responses = [
                subprocess.CompletedProcess(["cursor-agent", "--help"], 0, "safe help", ""),
                subprocess.CompletedProcess(
                    ["cursor-agent", "--list-models"],
                    0,
                    "claude-fable-5-thinking-high",
                    "",
                ),
            ]
            with (
                patch.object(backends.shutil, "which", return_value="/mock/cursor-agent"),
                patch.object(backends, "run_cmd", side_effect=responses),
            ):
                result = preflight_model(spec, Path(tmp))
        self.assertEqual(result["state"], "model_unavailable")
        self.assertFalse(result["model_available"])
        self.assertFalse(result["inference_attempted"])

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

    def test_sweep_model_panels_can_separate_creators_and_solvers(self) -> None:
        self.assertEqual(
            DEFAULT_MODELS,
            [
                "gpt-5.6-sol@high",
                "gpt-5.6-terra@xhigh",
                "agy:gemini-3.6-flash-high@high",
                "agy:gemini-3.7-flash-high@high",
                "agy:halcyon@high",
                "cursor:claude-opus-5@high",
            ],
        )
        creators, solvers = resolve_model_lists(None, None, None)
        self.assertEqual(creators, DEFAULT_MODELS)
        self.assertEqual(solvers, DEFAULT_MODELS)

    def test_experiment_010_rejects_any_non_frontier_panel_before_launch(self) -> None:
        exact = [
            call_artifact_id(spec.artifact_id, effective_effort(spec, "high"))
            for spec in map(parse_model_spec, FRONTIER_FOUR_MODELS)
        ]
        exact_five = [
            call_artifact_id(spec.artifact_id, effective_effort(spec, "high"))
            for spec in map(parse_model_spec, FRONTIER_FIVE_MODELS)
        ]
        current = ["one", "two", "three", "four", "five", "six"]
        self.assertEqual(
            resolve_panel_policy(Path("experiments/010_four_model_panel"), exact, exact, current, current),
            "benchbench.frontier-four/2026-08-01",
        )
        with self.assertRaisesRegex(ValueError, "Experiment 010 requires the exact"):
            resolve_panel_policy(
                Path("experiments/010_four_model_panel"),
                exact[:-1],
                exact,
                current,
                current,
            )
        self.assertEqual(
            resolve_panel_policy(Path("experiments/013_frontier_five"), exact_five, exact_five, current, current),
            "benchbench.frontier-five/2026-08-13",
        )
        self.assertEqual(
            resolve_panel_policy(Path("experiments/014_frontier_six"), current, current, current, current),
            "benchbench.frontier-six/2026-10-03",
        )

        creators, solvers = resolve_model_lists(
            ["gpt-5.2", "gpt-5.4"],
            ["gpt-5.4"],
            ["gpt-5.2", "gpt-5.4", "cursor:claude-opus"],
        )
        self.assertEqual(creators, ["gpt-5.4"])
        self.assertEqual(solvers, ["gpt-5.2", "gpt-5.4", "cursor:claude-opus"])

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
            with patch("run_broad_three_model_sweep.MODEL_SPECS", [spec]):
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
