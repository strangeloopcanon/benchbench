import json
import hashlib
import tempfile
import unittest
import os
import shlex
import sys
from contextlib import nullcontext
from pathlib import Path
from unittest.mock import patch

import run_broad_three_model_sweep as sweep
from benchbench_run_state import (
    call_artifact_id,
    create_source_snapshot,
    record_source_snapshot,
    require_new_run_root,
    verify_source_snapshot,
)
from benchbench_model_backends import parse_model_spec, run_cmd
from benchbench_sandbox import (
    antigravity_headless_permissions,
    isolated_provider_path,
    load_codex_broker_credentials,
    run_generated_command,
    SandboxUnavailable,
    sanitized_environment,
    sanitized_provider_environment,
)
from benchbench_schema import benchmark_package_digest, bundle_leaks, validate_answer_rows, validate_artifact_tree


def write_fixture(
    candidate: Path,
    *,
    leak: bool = False,
    nondeterministic: bool = False,
    scorer_leak: bool = False,
    legacy_score: bool = False,
) -> None:
    (candidate / "solver_bundle").mkdir(parents=True)
    for name in ("README.md", "benchmark_spec.json", "validation_report.md", "failure_modes.md"):
        (candidate / name).write_text("External solvability evidence lets a qualified solver identify deterministic answers. " * 3, encoding="utf-8")
    (candidate / "solver_bundle" / "README.md").write_text("Solve each public item from its visible evidence.", encoding="utf-8")
    generator = '''
import json
from pathlib import Path
rows = [{"id": f"i{n}", "answer": str(n)} for n in range(30)]
Path("solver_bundle").mkdir(parents=True, exist_ok=True)
Path("gold_private_sample.jsonl").write_text("".join(json.dumps(x)+"\\n" for x in rows))
Path("solver_bundle/items_private_sample.jsonl").write_text("".join(json.dumps({"id": x["id"], "prompt": "count"})+"\\n" for x in rows))
Path("solver_bundle/SOLVER_MANIFEST.json").write_text(json.dumps({"version": 1}))
Path("solver_bundle/README.md").write_text("Solve each public item from its visible evidence.")
'''
    if nondeterministic:
        generator += 'Path("solver_bundle/nonce.txt").write_text(str(__import__("time").time_ns()))\n'
    (candidate / "generator.py").write_text(generator, encoding="utf-8")
    rows = [{"id": f"i{n}", "answer": str(n)} for n in range(30)]
    (candidate / "gold_private_sample.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
    )
    (candidate / "solver_bundle" / "items_private_sample.jsonl").write_text(
        "".join(json.dumps({"id": row["id"], "prompt": "count"}) + "\n" for row in rows),
        encoding="utf-8",
    )
    (candidate / "solver_bundle" / "SOLVER_MANIFEST.json").write_text(
        json.dumps({"version": 1}), encoding="utf-8"
    )
    (candidate / "verifier.py").write_text("import sys\nsys.exit(0)\n", encoding="utf-8")
    (candidate / "scorer.py").write_text('''
import argparse, json
p=argparse.ArgumentParser(); p.add_argument("--gold"); p.add_argument("--predictions"); p.add_argument("--out"); a=p.parse_args()
g=[json.loads(x) for x in open(a.gold) if x.strip()]; q={x["id"]:x["answer"] for x in [json.loads(x) for x in open(a.predictions) if x.strip()]}
correct=sum(q.get(x["id"]) == x["answer"] for x in g)
payload={"total":len(g),"correct":correct,"accuracy":correct/len(g)}
if not ''' + repr(legacy_score) + ''':
 payload["schema_version"]=2
if ''' + repr(scorer_leak) + ''':
 payload["gold_rows"]=g
 print("TOP_SECRET_GOLD")
 print("TOP_SECRET_GOLD", file=__import__("sys").stderr)
open(a.out,"w").write(json.dumps(payload))
''', encoding="utf-8")
    if leak:
        (candidate / "solver_bundle" / "leak.jsonl").write_text('{"id":"i0","answer":"0"}\n', encoding="utf-8")


class RunnerIntegrityTests(unittest.TestCase):
    def test_prompt_input_digests_bind_exact_injected_text(self) -> None:
        self.assertEqual(
            sweep.BENCHMARK_LANDSCAPE_DIGEST,
            hashlib.sha256(sweep.BENCHMARK_LANDSCAPE.encode("utf-8")).hexdigest(),
        )
        self.assertEqual(
            sweep.PILOT_SUMMARY_DIGEST,
            hashlib.sha256(sweep.PILOT_SUMMARY.encode("utf-8")).hexdigest(),
        )

    def test_creator_and_repair_prompts_declare_controller_score_contract(self) -> None:
        for prompt in (sweep.CREATOR_PROMPT, sweep.REPAIR_PROMPT):
            self.assertIn("schema_version", prompt)
            self.assertIn("total", prompt)
            self.assertIn("correct", prompt)
            self.assertIn("accuracy", prompt)

    def test_antigravity_boundary_blocks_keychain_cli_and_token_recreation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            original_home = root / "original-home"
            token_dir = original_home / ".gemini" / "antigravity-cli"
            token_dir.mkdir(parents=True)
            (token_dir / "antigravity-oauth-token").write_text("oauth-canary", encoding="utf-8")
            binary_dir = root / "bin"
            binary_dir.mkdir()
            scratch = root / "scratch"
            scratch.mkdir()
            fake = binary_dir / "agy"
            fake.write_text(
                "#!/bin/sh\n"
                "config=\"$HOME/.gemini/antigravity-cli\"\n"
                "test \"$(cat \"$config/antigravity-oauth-token\")\" = oauth-canary || exit 30\n"
                "printf disposable > \"$config/installation_id\" || exit 31\n"
                "printf recreated > \"$config/antigravity-oauth-token\" 2>/dev/null && exit 32\n"
                "/usr/bin/security help >/dev/null 2>&1\n"
                "test $? -eq 126 || exit 33\n"
                "exit 0\n",
                encoding="utf-8",
            )
            fake.chmod(0o700)
            old_path = os.environ.get("PATH", "")
            old_home = os.environ.get("HOME")
            os.environ["PATH"] = f"{binary_dir}{os.pathsep}{old_path}"
            os.environ["HOME"] = str(original_home)
            try:
                with isolated_provider_path("agy", scratch):
                    settings = json.loads(
                        (
                            Path(os.environ["HOME"])
                            / ".gemini"
                            / "antigravity-cli"
                            / "settings.json"
                        ).read_text(encoding="utf-8")
                    )
                    self.assertEqual(
                        settings["permissions"]["allow"],
                        list(antigravity_headless_permissions(scratch)),
                    )
                    self.assertEqual(
                        settings["permissions"]["deny"],
                        [f"read_file({Path(os.environ['HOME']).resolve()})"],
                    )
                    self.assertFalse(settings["allowNonWorkspaceAccess"])
                    self.assertEqual(settings["toolPermission"], "always-proceed")
                    result = run_cmd(["agy"], scratch, timeout=20)
            finally:
                os.environ["PATH"] = old_path
                if old_home is None:
                    os.environ.pop("HOME", None)
                else:
                    os.environ["HOME"] = old_home
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_cursor_environment_fails_before_loading_token(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            provider_home = root / "home"; provider_home.mkdir()
            wrapper = root / "wrapper"; wrapper.mkdir()
            scratch_tmp = root / "tmp"; scratch_tmp.mkdir()
            with (
                patch("benchbench_sandbox.load_cursor_access_token") as load_token,
                self.assertRaises(SandboxUnavailable),
            ):
                sanitized_provider_environment(
                    {"HOME": "/real", "PATH": "/usr/bin"},
                    binary="cursor-agent",
                    provider_home=provider_home,
                    wrapper_root=wrapper,
                    scratch_tmp=scratch_tmp,
                )
            load_token.assert_not_called()

    def test_cursor_live_boundary_is_disabled_before_token_load(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            binary_dir = root / "bin"
            binary_dir.mkdir()
            scratch = root / "scratch"
            scratch.mkdir()
            fake = binary_dir / "cursor-agent"
            fake.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            fake.chmod(0o700)
            old_path = os.environ.get("PATH", "")
            os.environ["PATH"] = f"{binary_dir}{os.pathsep}{old_path}"
            try:
                with patch("benchbench_sandbox.load_cursor_access_token") as load_token:
                    with self.assertRaises(SandboxUnavailable):
                        with isolated_provider_path("cursor-agent", scratch):
                            pass
                    load_token.assert_not_called()
            finally:
                os.environ["PATH"] = old_path

    def test_answer_contract_rejects_partial_or_extra_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rows.jsonl"
            path.write_text('{"id":"x","answer":"a","extra":1}\n', encoding="utf-8")
            with self.assertRaises(ValueError):
                validate_answer_rows(path, count=1)
            path.write_text('{"id":"x","answer":{"amount":12.5}}\n', encoding="utf-8")
            self.assertEqual(validate_answer_rows(path, count=1)[0]["answer"], {"amount": 12.5})

    def test_bundle_leak_detects_answer_for_same_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp) / "bundle"; bundle.mkdir()
            (bundle / "items.jsonl").write_text('{"id":"x","answer":"secret"}\n', encoding="utf-8")
            self.assertTrue(bundle_leaks(bundle, [{"id":"x", "answer":"secret"}]))

    def test_bundle_leak_detects_csv_text_and_nested_answer_maps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp) / "bundle"
            bundle.mkdir()
            gold = [{"id": "x", "answer": "secret"}, {"id": "y", "answer": 7}]
            (bundle / "table.csv").write_text("id,value\nx,secret\n", encoding="utf-8")
            (bundle / "notes.txt").write_text("y: 7\n", encoding="utf-8")
            (bundle / "nested.json").write_text(
                json.dumps({"metadata": {"answers_by_item": {"x": "secret"}}}),
                encoding="utf-8",
            )
            (bundle / "records.yaml").write_text(
                "- id: x\n  context: public\n  answer: secret\n",
                encoding="utf-8",
            )
            matches = bundle_leaks(bundle, gold)
            self.assertTrue(any("table.csv" in match for match in matches), matches)
            self.assertTrue(any("notes.txt" in match for match in matches), matches)
            self.assertTrue(any("nested.json" in match for match in matches), matches)
            self.assertTrue(any("records.yaml" in match for match in matches), matches)

    def test_bundle_leak_rejects_solution_bearing_filenames(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp) / "bundle"
            bundle.mkdir()
            (bundle / "solutions.yaml").write_text("redacted: true\n", encoding="utf-8")
            (bundle / "solution.md").write_text("x\n\nsecret\n", encoding="utf-8")
            self.assertIn(
                "prohibited-path:solutions.yaml",
                bundle_leaks(bundle, [{"id": "x", "answer": "secret"}]),
            )
            self.assertIn(
                "prohibited-path:solution.md",
                bundle_leaks(bundle, [{"id": "x", "answer": "secret"}]),
            )

    def test_local_validation_runs_in_scratch_and_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp) / "candidate"; write_fixture(candidate)
            result = sweep.local_validate(candidate)
            self.assertTrue(result["valid"], result["report"])
            self.assertFalse((candidate / "predictions_gold_controller.jsonl").exists())
            self.assertFalse((candidate / "score_gold_controller.json").exists())
            self.assertFalse((candidate / "controller_validation_report.txt").exists())

    def test_local_validation_rejects_legacy_score_schema(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp) / "candidate"
            write_fixture(candidate, legacy_score=True)
            result = sweep.local_validate(candidate)
            self.assertFalse(result["valid"])
            self.assertIsNone(result["gold_summary"])
            self.assertIsNone(result["wrong_summary"])

    def test_local_validation_accepts_strict_v2_score_schema(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp) / "candidate"
            write_fixture(candidate)
            result = sweep.local_validate(candidate)
            self.assertTrue(result["valid"], result["report"])
            self.assertEqual(result["gold_summary"], {"total": 30, "correct": 30, "accuracy": 1.0})

    def test_local_validation_rejects_public_answer_leak_and_nondeterminism(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp) / "candidate"; write_fixture(candidate, leak=True, nondeterministic=True)
            result = sweep.local_validate(candidate)
            self.assertFalse(result["valid"])
            self.assertTrue(result["leak_matches"] or "deterministic_generated_payload_digest: False" in result["report"])

    def test_generated_command_reports_never_retain_private_stdout_or_stderr(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp) / "candidate"
            write_fixture(candidate, scorer_leak=True)
            result = sweep.local_validate(candidate)
            self.assertTrue(result["valid"], result["report"])
            self.assertNotIn("TOP_SECRET_GOLD", result["report"])
            self.assertNotIn("gold_rows", result["report"])
            self.assertIn("stdout_sha256", result["report"])

    def test_solver_publishes_only_allowlisted_normalized_score(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate = (
                root
                / "run"
                / "candidate_created_by_codex__creator__effort_high"
                / "attempt_0001"
                / "artifact"
            )
            write_fixture(candidate, scorer_leak=True)
            old_run_dir = sweep.RUN_DIR
            sweep.RUN_DIR = root / "run"
            sweep.RUN_DIR.mkdir(exist_ok=True)

            def fake_run_model(spec, prompt, out_path, cwd, effort, timeout):
                rows = [{"id": f"i{n}", "answer": str(n)} for n in range(30)]
                out_path.write_text(
                    "".join(json.dumps(row) + "\n" for row in rows),
                    encoding="utf-8",
                )
                return {
                    "model": spec.name,
                    "display_model": spec.display_name,
                    "provider": spec.provider,
                    "artifact_id": spec.artifact_id,
                    "returncode": 0,
                    "tokens_used": 1,
                    "out_path": str(out_path),
                }

            try:
                with (
                    patch.object(sweep, "isolated_provider_path", return_value=nullcontext()),
                    patch.object(sweep, "run_model", side_effect=fake_run_model),
                    patch.object(sweep, "freeze_call_evidence"),
                ):
                    result = sweep.run_solver(
                        "creator",
                        parse_model_spec("gpt-5.6-sol"),
                        candidate,
                    )
            finally:
                sweep.RUN_DIR = old_run_dir

            self.assertEqual(result["cell_state"], "success", result)
            score_path = Path(result["score_path"])
            published = json.loads(score_path.read_text(encoding="utf-8"))
            self.assertEqual(
                set(published),
                {
                    "schema_version",
                    "total",
                    "correct",
                    "accuracy",
                    "invocation_id",
                    "candidate_digest",
                    "gold_digest",
                    "prediction_digest",
                },
            )
            self.assertFalse(score_path.with_suffix(".raw.txt").exists())

    def test_solver_rejects_legacy_candidate_score_schema(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate = root / "run" / "candidate" / "attempt_0001" / "artifact"
            write_fixture(candidate, legacy_score=True)
            old_run_dir = sweep.RUN_DIR
            sweep.RUN_DIR = root / "run"

            def fake_run_model(spec, prompt, out_path, cwd, effort, timeout):
                out_path.write_text(
                    "".join(json.dumps({"id": f"i{n}", "answer": str(n)}) + "\n" for n in range(30)),
                    encoding="utf-8",
                )
                return {"returncode": 0, "tokens_used": 1, "out_path": str(out_path)}

            try:
                with (
                    patch.object(sweep, "isolated_provider_path", return_value=nullcontext()),
                    patch.object(sweep, "run_model", side_effect=fake_run_model),
                    patch.object(sweep, "freeze_call_evidence"),
                ):
                    result = sweep.run_solver("creator", parse_model_spec("gpt-5.6-sol"), candidate)
            finally:
                sweep.RUN_DIR = old_run_dir

            self.assertEqual(result["cell_state"], "invalid_score", result)
            self.assertFalse(Path(result["score_path"]).exists())

    def test_local_validation_rejects_generated_solver_bundle_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp) / "candidate"
            write_fixture(candidate)
            with (candidate / "generator.py").open("a", encoding="utf-8") as handle:
                handle.write(
                    "Path('solver_bundle/reference_notes.txt').symlink_to('../gold_private_sample.jsonl')\n"
                )
            result = sweep.local_validate(candidate)
            self.assertFalse(result["valid"])
            self.assertIn("symbolic link", result["report"])

    def test_local_validation_rejects_unfrozen_generated_sample(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp) / "candidate"
            write_fixture(candidate)
            (candidate / "gold_private_sample.jsonl").unlink()
            (candidate / "solver_bundle" / "items_private_sample.jsonl").unlink()
            result = sweep.local_validate(candidate)
            self.assertFalse(result["valid"])
            self.assertIn("frozen_generated_payload_digest_match: False", result["report"])

    def test_nonempty_run_root_is_never_reused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "run"
            require_new_run_root(root, {"models": ["codex__gpt_5_5"]})
            with self.assertRaises(RuntimeError):
                require_new_run_root(root, {"models": ["codex__gpt_5_5"]})
            with self.assertRaises(RuntimeError):
                require_new_run_root(Path(tmp) / "other", {}, resume=True)

    def test_source_snapshot_is_allowlisted_bound_to_state_and_verifiable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source"
            source.mkdir()
            (source / "runner.py").write_text("print('frozen')\n", encoding="utf-8")
            (source / "uv.lock").write_text("version = 1\n", encoding="utf-8")
            (source / ".env").write_text("API_KEY=must-not-copy\n", encoding="utf-8")
            (source / "experiments").mkdir()
            (source / "experiments" / "private.json").write_text("secret\n", encoding="utf-8")
            run_root = Path(tmp) / "run-root"
            require_new_run_root(run_root, {"models": ["model"]})

            snapshot = create_source_snapshot(source, run_root, ("runner.py", "uv.lock"))
            record_source_snapshot(run_root, snapshot)

            state = json.loads((run_root / "run_state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["source_snapshot"]["digest"], snapshot["digest"])
            self.assertEqual(
                verify_source_snapshot(run_root, expected_digest=snapshot["digest"])["digest"],
                snapshot["digest"],
            )
            self.assertFalse((run_root / "source_snapshot" / ".env").exists())
            self.assertFalse((run_root / "source_snapshot" / "experiments").exists())

            (run_root / "source_snapshot" / "runner.py").write_text("tampered\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "digest mismatch"):
                verify_source_snapshot(run_root, expected_digest=snapshot["digest"])

    def test_effort_qualified_ids_do_not_collide(self) -> None:
        self.assertNotEqual(call_artifact_id("codex__gpt_5_6_sol", "low"), call_artifact_id("codex__gpt_5_6_sol", "high"))

    def test_budget_stops_when_token_telemetry_is_missing(self) -> None:
        self.assertTrue(sweep.budget_allows_call([], 100))
        self.assertTrue(sweep.budget_allows_call([{"tokens_used": 10}], 100))
        self.assertFalse(sweep.budget_allows_call([{"tokens_used": 0}], 100))
        self.assertTrue(sweep.budget_allows_call([{"tokens_used": 0}], 6_000_000))
        self.assertFalse(sweep.budget_allows_call([{"tokens_used": 100}], 100))
        self.assertEqual(
            sweep.charged_tokens([{"tokens_used": 10}, {"tokens_used": 0}]),
            5_000_010,
        )

    def test_benchmark_digest_covers_creator_files_even_with_solver_evidence_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp)
            (candidate / "generator.py").write_text("# package\n", encoding="utf-8")
            before = benchmark_package_digest(candidate)
            (candidate / "predictions_solver_codex__model__effort_high.jsonl").write_text(
                '{"id":"x","answer":"a"}\n', encoding="utf-8"
            )
            (candidate / "score_solver_codex__model__effort_high.json").write_text(
                '{"schema_version":2,"total":1,"correct":1,"accuracy":1.0}\n', encoding="utf-8"
            )
            self.assertNotEqual(before, benchmark_package_digest(candidate))

    def test_artifact_tree_rejects_symlinks_without_following_them(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            private = sweep.ROOT / "benchbench_model_backends.py"
            (root / "credential-link").symlink_to(private)
            with self.assertRaisesRegex(ValueError, "symbolic link"):
                validate_artifact_tree(root)

    def test_artifact_tree_rejects_hard_links(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            source.write_text("private", encoding="utf-8")
            os.link(source, root / "linked")
            with self.assertRaisesRegex(ValueError, "hard-linked"):
                validate_artifact_tree(root)

    def test_real_seatbelt_can_read_scratch_but_denies_private_canary_and_env(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as other_tmp:
            root = Path(tmp)
            scratch = root / "scratch"; scratch.mkdir()
            # A real checkout file is outside the /private scratch tree and
            # represents the private-gold boundary a blind solver must not cross.
            secret = sweep.ROOT / "benchbench_model_backends.py"
            (scratch / "visible.txt").write_text("public", encoding="utf-8")
            concurrent_secret = Path(other_tmp) / "other-run-gold.jsonl"
            concurrent_secret.write_text('{"id":"private","answer":"secret"}\n', encoding="utf-8")
            (scratch / "probe.py").write_text(
                "import os, pathlib, subprocess, sys\n"
                "assert pathlib.Path('visible.txt').read_text() == 'public'\n"
                "assert os.getenv('BENCHBENCH_TEST_SECRET') is None\n"
                f"for path in ({str(secret)!r}, {str(concurrent_secret)!r}):\n"
                " try:\n"
                "  pathlib.Path(path).read_text()\n"
                " except PermissionError:\n"
                "  continue\n"
                " raise AssertionError(f'private path was readable: {path}')\n"
                "try:\n"
                " subprocess.run(['/bin/sh', '-c', 'exit 0'], check=True)\n"
                "except (PermissionError, OSError):\n"
                " pass\n"
                "else:\n"
                " raise AssertionError('generated code could spawn a shell')\n",
                encoding="utf-8",
            )
            old = os.environ.get("BENCHBENCH_TEST_SECRET")
            os.environ["BENCHBENCH_TEST_SECRET"] = "must-not-cross"
            try:
                result = run_generated_command([sweep.SANDBOX_PYTHON, "probe.py"], scratch, timeout=20)
            finally:
                if old is None:
                    os.environ.pop("BENCHBENCH_TEST_SECRET", None)
                else:
                    os.environ["BENCHBENCH_TEST_SECRET"] = old
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_outer_provider_boundary_denies_checkout_reads(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            binary_dir = root / "bin"; binary_dir.mkdir()
            scratch = root / "scratch"; scratch.mkdir()
            (scratch / "visible.txt").write_text("public", encoding="utf-8")
            fake = binary_dir / "fake-provider"
            fake.write_text(
                "#!/bin/sh\n"
                "test \"$(cat visible.txt)\" = public || exit 4\n"
                "test -r /private/etc/ssl/cert.pem || exit 12\n"
                "test -z \"${BENCHBENCH_TEST_SECRET+x}\" || exit 8\n"
                f"cat {str(sweep.ROOT / 'benchbench_model_backends.py')!r} >/dev/null 2>&1 && exit 9\n"
                f"cat {str(Path.home() / '.codex' / 'memories' / 'memory_summary.md')!r} >/dev/null 2>&1 && exit 10\n"
                "/bin/ps eww -p \"$PPID\" >/dev/null 2>&1 && exit 11\n"
                "exit 0\n",
                encoding="utf-8",
            )
            fake.chmod(0o700)
            old_path = os.environ.get("PATH", "")
            old_secret = os.environ.get("BENCHBENCH_TEST_SECRET")
            os.environ["PATH"] = f"{binary_dir}{os.pathsep}{old_path}"
            os.environ["BENCHBENCH_TEST_SECRET"] = "must-not-cross"
            try:
                with isolated_provider_path("fake-provider", scratch):
                    result = run_cmd(["fake-provider"], scratch, timeout=20)
            finally:
                os.environ["PATH"] = old_path
                if old_secret is None:
                    os.environ.pop("BENCHBENCH_TEST_SECRET", None)
                else:
                    os.environ["BENCHBENCH_TEST_SECRET"] = old_secret
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_cursor_never_launches_even_when_binary_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            binary_dir = root / "bin"; binary_dir.mkdir()
            scratch = root / "scratch"; scratch.mkdir()
            fake = binary_dir / "cursor-agent"
            fake.write_text(
                "#!/bin/sh\n"
                "test -z \"${BENCHBENCH_CURSOR_BROKER_TOKEN+x}\" || exit 20\n"
                "/usr/bin/security find-generic-password -s cursor-access-token -w >/dev/null 2>&1 && exit 21\n"
                "/bin/ps eww -p \"$PPID\" >/dev/null 2>&1 && exit 22\n"
                "exit 0\n",
                encoding="utf-8",
            )
            fake.chmod(0o700)
            old_path = os.environ.get("PATH", "")
            os.environ["PATH"] = f"{binary_dir}{os.pathsep}{old_path}"
            try:
                with patch("benchbench_sandbox.load_cursor_access_token") as load_token:
                    with self.assertRaises(SandboxUnavailable):
                        with isolated_provider_path("cursor-agent", scratch):
                            pass
                    load_token.assert_not_called()
            finally:
                os.environ["PATH"] = old_path

    def test_codex_boundary_denies_parent_environment_and_keychain_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            binary_dir = root / "bin"
            binary_dir.mkdir()
            scratch = root / "scratch"
            scratch.mkdir()
            (scratch / "probe.py").write_text(
                "import ctypes, ctypes.util, sys\n"
                "pid = int(sys.argv[1])\n"
                "libc = ctypes.CDLL(ctypes.util.find_library('c'), use_errno=True)\n"
                "for selector in (38, 49):\n"
                " mib = (ctypes.c_int * 3)(1, selector, pid)\n"
                " size = ctypes.c_size_t(0)\n"
                " rc = libc.sysctl(mib, 3, None, ctypes.byref(size), None, 0)\n"
                " if rc == 0:\n"
                "  buf = ctypes.create_string_buffer(size.value)\n"
                "  rc = libc.sysctl(mib, 3, buf, ctypes.byref(size), None, 0)\n"
                "  if rc == 0 and b'broker-secret-canary' in buf.raw:\n"
                "   raise SystemExit(12)\n",
                encoding="utf-8",
            )
            fake = binary_dir / "codex"
            fake.write_text(
                "#!/bin/sh\n"
                "/usr/sbin/scutil --dns >/dev/null || exit 13\n"
                "/usr/bin/security help >/dev/null 2>&1\n"
                "test $? -eq 126 || exit 14\n"
                "/usr/bin/env -i PATH=/usr/bin:/bin "
                f"{shlex.quote(sys.executable)} probe.py \"$$\"\n",
                encoding="utf-8",
            )
            fake.chmod(0o700)
            old_path = os.environ.get("PATH", "")
            old_token = os.environ.get("BENCHBENCH_CODEX_BEARER_TOKEN")
            old_account = os.environ.get("BENCHBENCH_CODEX_ACCOUNT_ID")
            os.environ["PATH"] = f"{binary_dir}{os.pathsep}{old_path}"
            os.environ["BENCHBENCH_CODEX_BEARER_TOKEN"] = "broker-secret-canary"
            os.environ["BENCHBENCH_CODEX_ACCOUNT_ID"] = "account-canary"
            try:
                with isolated_provider_path("codex", scratch):
                    result = run_cmd(["codex"], scratch, timeout=20)
            finally:
                os.environ["PATH"] = old_path
                if old_token is None:
                    os.environ.pop("BENCHBENCH_CODEX_BEARER_TOKEN", None)
                else:
                    os.environ["BENCHBENCH_CODEX_BEARER_TOKEN"] = old_token
                if old_account is None:
                    os.environ.pop("BENCHBENCH_CODEX_ACCOUNT_ID", None)
                else:
                    os.environ["BENCHBENCH_CODEX_ACCOUNT_ID"] = old_account
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_codex_broker_uses_parent_environment_without_staging_credentials(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            original = root / "original"
            codex_home = original / ".codex"
            codex_home.mkdir(parents=True)
            (codex_home / "auth.json").write_text(
                json.dumps(
                    {
                        "auth_mode": "chatgpt",
                        "OPENAI_API_KEY": None,
                        "tokens": {
                            "access_token": "short-lived",
                            "account_id": "account",
                            "id_token": "identity",
                            "refresh_token": "must-not-cross",
                        },
                    }
                ),
                encoding="utf-8",
            )
            (codex_home / "memories").mkdir()
            (codex_home / "memories" / "private.md").write_text("private", encoding="utf-8")
            provider_home = root / "provider-home"
            provider_home.mkdir()
            wrapper_root = root / "wrapper"
            wrapper_root.mkdir()
            scratch_tmp = root / "scratch-tmp"
            scratch_tmp.mkdir()
            original_environment = {"HOME": str(original), "CODEX_HOME": str(codex_home)}
            token, account_id = load_codex_broker_credentials(original_environment)
            environment = sanitized_provider_environment(
                original_environment,
                binary="codex",
                provider_home=provider_home,
                wrapper_root=wrapper_root,
                scratch_tmp=scratch_tmp,
            )
            self.assertEqual((token, account_id), ("short-lived", "account"))
            self.assertEqual(environment["BENCHBENCH_CODEX_BEARER_TOKEN"], "short-lived")
            self.assertEqual(environment["BENCHBENCH_CODEX_ACCOUNT_ID"], "account")
            self.assertNotIn("BENCHBENCH_CODEX_BEARER_TOKEN", sanitized_environment())
            self.assertFalse(any(provider_home.rglob("auth.json")))
            self.assertFalse(any(provider_home.rglob("private.md")))

    def test_candidate_status_requires_complete_cells_when_missing(self) -> None:
        original = sweep.MODEL_SPECS
        try:
            sweep.MODEL_SPECS = [object(), object()]
            self.assertEqual(sweep.candidate_status([{"total": 30, "correct": 1, "cell_state": "success"}]), "incomplete_panel")
            self.assertEqual(sweep.candidate_status([{"total": 30, "correct": 1, "cell_state": "success"}, {"total": 30, "correct": 2, "cell_state": "backend_error"}]), "incomplete_panel")
        finally:
            sweep.MODEL_SPECS = original

    def test_legacy_unqualified_scores_are_display_only(self) -> None:
        original = sweep.MODEL_SPECS
        try:
            sweep.MODEL_SPECS = [sweep.parse_model_spec("gpt-5.6-sol")]
            with tempfile.TemporaryDirectory() as tmp:
                candidate = Path(tmp)
                (candidate / "score_solver_gpt_5_6_sol.json").write_text(
                    '{"total":30,"correct":1,"accuracy":0.03333333333333333}\n',
                    encoding="utf-8",
                )
                cells, _scores, _maximum, status = sweep.solver_score_cells(candidate)
                self.assertEqual(cells, ["1/30"])
                self.assertEqual(status, "historical_noncanonical")
        finally:
            sweep.MODEL_SPECS = original

    def test_creator_preplanted_qualified_score_is_ignored(self) -> None:
        original = sweep.MODEL_SPECS
        try:
            spec = sweep.parse_model_spec("gpt-5.6-sol")
            sweep.MODEL_SPECS = [spec]
            with tempfile.TemporaryDirectory() as tmp:
                candidate = Path(tmp)
                qualified = sweep.call_artifact_id(spec.artifact_id, sweep.SOLVER_EFFORT)
                (candidate / f"score_solver_{qualified}.json").write_text(
                    '{"schema_version":2,"total":30,"correct":1,"accuracy":0.03333333333333333,'
                    '"candidate_digest":"fake","gold_digest":"fake","prediction_digest":"fake"}\n',
                    encoding="utf-8",
                )
                cells, _scores, _maximum, status = sweep.solver_score_cells(candidate)
                self.assertEqual(cells, ["NA"])
                self.assertEqual(status, "incomplete_panel")
        finally:
            sweep.MODEL_SPECS = original
