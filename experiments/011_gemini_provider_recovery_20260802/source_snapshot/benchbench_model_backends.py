#!/usr/bin/env python3
"""Model backend helpers for BenchBench runners."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import tempfile
from typing import Any


CODEX_BROKER_PROVIDER_ID = "benchbench_chatgpt"
CODEX_BROKER_TOKEN_ENV = "BENCHBENCH_CODEX_BEARER_TOKEN"
CODEX_BROKER_ACCOUNT_ENV = "BENCHBENCH_CODEX_ACCOUNT_ID"


def codex_broker_config_args() -> list[str]:
    """Return a credential-file-free ChatGPT provider configuration.

    The trusted Codex parent obtains its bearer token by running ``printenv``.
    Model-created tools receive ``shell_environment_policy.inherit=none`` and
    therefore cannot invoke the same command to recover the credential.
    """

    prefix = f"model_providers.{CODEX_BROKER_PROVIDER_ID}"
    values = [
        f'model_provider="{CODEX_BROKER_PROVIDER_ID}"',
        f'{prefix}.name="BenchBench ChatGPT"',
        f'{prefix}.base_url="https://chatgpt.com/backend-api/codex"',
        f'{prefix}.wire_api="responses"',
        f'{prefix}.auth.command="/usr/bin/printenv"',
        f'{prefix}.auth.args=["{CODEX_BROKER_TOKEN_ENV}"]',
        f"{prefix}.auth.refresh_interval_ms=0",
        f'{prefix}.env_http_headers={{"ChatGPT-Account-ID" = "{CODEX_BROKER_ACCOUNT_ENV}"}}',
        f"{prefix}.requires_openai_auth=false",
    ]
    return [part for value in values for part in ("-c", value)]


KNOWN_ANTIGRAVITY_MODELS = {
    "current": (None, "Antigravity current model"),
    # A contained live canary established the provider's runtime-log label;
    # keep it bound so a silent resolver fallback becomes a typed mismatch.
    "gemini-3.6-flash": ("Gemini 3.6 Flash (High)", "Gemini 3.6 Flash (High)"),
    "gemini-3.6-flash-high": ("Gemini 3.6 Flash (High)", "Gemini 3.6 Flash (High)"),
    "gemini-3.5-flash-high": ("Gemini 3.5 Flash (High)", "Gemini 3.5 Flash (High)"),
    "gemini-3.1-pro": ("Gemini 3.1 Pro (High)", "Gemini 3.1 Pro (High)"),
    "gemini-3.1-pro-high": ("Gemini 3.1 Pro (High)", "Gemini 3.1 Pro (High)"),
    "gemini-3.1-pro-low": ("Gemini 3.1 Pro (Low)", "Gemini 3.1 Pro (Low)"),
    "claude-sonnet-4.6-thinking": ("Claude Sonnet 4.6 (Thinking)", "Claude Sonnet 4.6 (Thinking)"),
    "claude-sonnet-4.6": ("Claude Sonnet 4.6 (Thinking)", "Claude Sonnet 4.6 (Thinking)"),
    "claude-sonnet": ("Claude Sonnet 4.6 (Thinking)", "Claude Sonnet 4.6 (Thinking)"),
    "claude-opus-4.6-thinking": ("Claude Opus 4.6 (Thinking)", "Claude Opus 4.6 (Thinking)"),
    "claude-opus-4.6": ("Claude Opus 4.6 (Thinking)", "Claude Opus 4.6 (Thinking)"),
    "claude-opus": ("Claude Opus 4.6 (Thinking)", "Claude Opus 4.6 (Thinking)"),
}

# CLI-facing identifiers are distinct from friendly aliases.  The aliases are
# retained in historical sweep manifests, while `agy models` exposes the
# concrete identifiers below.
ANTIGRAVITY_CLI_MODELS = {
    "gemini-3.6-flash": "gemini-3.6-flash-high",
    "gemini-3.6-flash-high": "gemini-3.6-flash-high",
    "gemini-3.5-flash-high": "gemini-3.5-flash-high",
    "gemini-3.1-pro": "gemini-3.1-pro-high",
    "gemini-3.1-pro-high": "gemini-3.1-pro-high",
    "gemini-3.1-pro-low": "gemini-3.1-pro-low",
    "claude-sonnet-4.6-thinking": "claude-sonnet-4-6",
    "claude-sonnet-4.6": "claude-sonnet-4-6",
    "claude-sonnet": "claude-sonnet-4-6",
    "claude-opus-4.6-thinking": "claude-opus-4-6-thinking",
    "claude-opus-4.6": "claude-opus-4-6-thinking",
    "claude-opus": "claude-opus-4-6-thinking",
}

KNOWN_CLAUDE_MODELS = {
    "sonnet": ("sonnet", "Claude Sonnet"),
    "opus": ("opus", "Claude Opus"),
    "haiku": ("haiku", "Claude Haiku"),
    "claude-sonnet-4-6": ("claude-sonnet-4-6", "Claude Sonnet 4.6"),
    "claude-opus-4-6": ("claude-opus-4-6", "Claude Opus 4.6"),
    "claude-haiku-4-5": ("claude-haiku-4-5", "Claude Haiku 4.5"),
}

KNOWN_CURSOR_MODELS = {
    "claude-opus-5": ("claude-opus-5-thinking-high", "Claude Opus 5 Thinking (High)"),
    "opus-5": ("claude-opus-5-thinking-high", "Claude Opus 5 Thinking (High)"),
    "claude-opus-5-thinking-high": ("claude-opus-5-thinking-high", "Claude Opus 5 Thinking (High)"),
    "claude-opus": ("claude-4.6-opus-high-thinking", "Claude Opus 4.6 Thinking"),
    "opus": ("claude-4.6-opus-high-thinking", "Claude Opus 4.6 Thinking"),
    "claude-opus-4.6-thinking": ("claude-4.6-opus-high-thinking", "Claude Opus 4.6 Thinking"),
    "claude-4.6-opus-high-thinking": ("claude-4.6-opus-high-thinking", "Claude Opus 4.6 Thinking"),
    "claude-opus-4.7-thinking-high": ("claude-opus-4-7-thinking-high", "Claude Opus 4.7 High Thinking"),
    "claude-opus-4-7-thinking-high": ("claude-opus-4-7-thinking-high", "Claude Opus 4.7 High Thinking"),
    "opus-4.7-thinking-high": ("claude-opus-4-7-thinking-high", "Claude Opus 4.7 High Thinking"),
    "fable": ("claude-fable-5-thinking-high", "Claude Fable 5 Thinking"),
    "fable-5": ("claude-fable-5-thinking-high", "Claude Fable 5 Thinking"),
    "claude-fable-5": ("claude-fable-5-thinking-high", "Claude Fable 5 Thinking"),
    "claude-fable-5-thinking-high": ("claude-fable-5-thinking-high", "Claude Fable 5 Thinking"),
    "fable-xhigh": ("claude-fable-5-thinking-xhigh", "Claude Fable 5 Extra High Thinking"),
    "claude-fable-5-thinking-xhigh": ("claude-fable-5-thinking-xhigh", "Claude Fable 5 Extra High Thinking"),
}

DEFAULT_CLAUDE_MAX_BUDGET_USD = "25"

PROVIDER_BINARIES = {
    "codex": "codex",
    "antigravity": "agy",
    "claude": "claude",
    "cursor": "cursor-agent",
}


@dataclass(frozen=True)
class ModelSpec:
    """A model plus the local runner that can invoke it."""

    name: str
    provider: str
    display_name: str
    codex_model: str | None = None
    antigravity_model: str | None = None
    antigravity_expected_label: str | None = None
    claude_model: str | None = None
    cursor_model: str | None = None
    reasoning_effort: str | None = None

    @property
    def agent_label(self) -> str:
        if self.provider == "codex":
            return f"{self.display_name}+Codex"
        if self.provider == "antigravity":
            return f"{self.display_name}+Antigravity"
        if self.provider == "claude":
            return f"{self.display_name}+Claude Code"
        if self.provider == "cursor":
            return f"{self.display_name}+Cursor"
        return self.display_name

    @property
    def concrete_model_id(self) -> str:
        """Return the exact model identifier passed to the provider CLI."""

        if self.provider == "codex":
            return self.codex_model or self.name
        if self.provider == "antigravity":
            return self.antigravity_model or self.name
        if self.provider == "claude":
            return self.claude_model or self.name
        if self.provider == "cursor":
            return self.cursor_model or self.name
        raise ValueError(f"Unsupported model provider: {self.provider}")

    @property
    def artifact_id(self) -> str:
        """Return the concrete provider/model identifier used in result paths.

        A model name alone is not an identity: for example, ``gpt-5.2`` can
        be invoked through both Codex and Cursor. Aliases that resolve to the
        same provider model must also collapse to one identity so they cannot
        evade duplicate-panel checks.
        """

        return f"{safe_name(self.provider)}__{safe_name(self.concrete_model_id)}"


def safe_name(name: str) -> str:
    """Return a stable filesystem slug for model and benchmark identifiers."""

    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", name.strip().lower()).strip("_")
    return cleaned or "model"


def provider_binary(spec: ModelSpec) -> str:
    """Return the executable name for a provider, without resolving PATH."""

    try:
        return PROVIDER_BINARIES[spec.provider]
    except KeyError as exc:
        raise ValueError(f"Unsupported model provider: {spec.provider}") from exc


def requested_provider_model(spec: ModelSpec) -> str:
    """Return the exact model token passed to the provider CLI."""

    return spec.concrete_model_id


KNOWN_REASONING_EFFORTS = {"none", "minimal", "low", "medium", "high", "xhigh", "max", "ultra"}


def effective_effort(spec: ModelSpec, fallback: str) -> str:
    """Return a model-local effort override or the phase fallback."""

    return spec.reasoning_effort or fallback


def parse_model_spec(value: str) -> ModelSpec:
    """Parse a model spec.

    Unprefixed values are Codex model names, preserving the historical runner
    behavior. Antigravity specs use `agy:<model>` or `antigravity:<model>`.
    Claude Code specs use `claude:<model>` or `anthropic:<model>`.
    Cursor specs use `cursor:<model>`.
    Antigravity receives the requested model explicitly on every invocation;
    its log is retained as provider provenance and checked after the run.
    """

    raw = value.strip()
    reasoning_effort = None
    if "@" in raw:
        raw, reasoning_effort = raw.rsplit("@", 1)
        raw = raw.strip()
        reasoning_effort = reasoning_effort.strip().lower()
        if reasoning_effort not in KNOWN_REASONING_EFFORTS:
            raise ValueError(f"Unsupported reasoning effort override: {reasoning_effort or '<empty>'}")
    lowered = raw.lower()
    for prefix in ("agy:", "antigravity:"):
        if lowered.startswith(prefix):
            model_id = lowered[len(prefix) :].strip()
            expected, display = KNOWN_ANTIGRAVITY_MODELS.get(
                model_id,
                (None, raw[len(prefix) :].strip() or "Antigravity current model"),
            )
            return ModelSpec(
                name=model_id or "current",
                provider="antigravity",
                display_name=display,
                # Unknown names are still passed explicitly so a typo fails at
                # the provider instead of silently invoking the user's current
                # selection under a false identity.
                antigravity_model=ANTIGRAVITY_CLI_MODELS.get(model_id, model_id or None),
                antigravity_expected_label=expected,
                reasoning_effort=reasoning_effort,
            )
    for prefix in ("claude:", "anthropic:"):
        if lowered.startswith(prefix):
            requested = raw[len(prefix) :].strip()
            model_id = requested.lower() or "sonnet"
            claude_model, display = KNOWN_CLAUDE_MODELS.get(
                model_id,
                (requested or "sonnet", requested or "Claude Sonnet"),
            )
            return ModelSpec(
                name=model_id,
                provider="claude",
                display_name=display,
                claude_model=claude_model,
                reasoning_effort=reasoning_effort,
            )
    for prefix in ("cursor:", "cursor-agent:"):
        if lowered.startswith(prefix):
            requested = raw[len(prefix) :].strip()
            model_id = requested.lower() or "claude-opus"
            cursor_model, display = KNOWN_CURSOR_MODELS.get(
                model_id,
                (requested or "claude-4.6-opus-high-thinking", requested or "Cursor model"),
            )
            return ModelSpec(
                name=model_id,
                provider="cursor",
                display_name=display,
                cursor_model=cursor_model,
                reasoning_effort=reasoning_effort,
            )
    return ModelSpec(
        name=raw,
        provider="codex",
        display_name=raw,
        codex_model=raw,
        reasoning_effort=reasoning_effort,
    )


def parse_tokens(text: str) -> int:
    matches = re.findall(r"tokens used\s+(\d[\d,]*)", text)
    return int(matches[-1].replace(",", "")) if matches else 0


def parse_antigravity_selected_label(log_text: str) -> str | None:
    matches = re.findall(r'Propagating selected model override to backend: label="([^"]+)"', log_text)
    return matches[-1] if matches else None


def claude_tokens_used(data: dict[str, Any]) -> int:
    model_usage = data.get("modelUsage")
    if isinstance(model_usage, dict):
        total = 0
        for usage_item in model_usage.values():
            if not isinstance(usage_item, dict):
                continue
            total += sum(
                int(usage_item.get(key) or 0)
                for key in [
                    "inputTokens",
                    "cacheCreationInputTokens",
                    "cacheReadInputTokens",
                    "outputTokens",
                ]
            )
        if total:
            return total

    usage = data.get("usage")
    if not isinstance(usage, dict):
        return 0
    return sum(
        int(usage.get(key) or 0)
        for key in [
            "input_tokens",
            "cache_creation_input_tokens",
            "cache_read_input_tokens",
            "output_tokens",
        ]
    )


def claude_cache_summary(data: dict[str, Any]) -> dict[str, int]:
    usage = data.get("usage")
    if isinstance(usage, dict):
        summary = {
            "cache_creation_input_tokens": int(usage.get("cache_creation_input_tokens") or 0),
            "cache_read_input_tokens": int(usage.get("cache_read_input_tokens") or 0),
        }
        if summary["cache_creation_input_tokens"] or summary["cache_read_input_tokens"]:
            return summary

    model_usage = data.get("modelUsage")
    if isinstance(model_usage, dict):
        return {
            "cache_creation_input_tokens": sum(
                int(item.get("cacheCreationInputTokens") or 0)
                for item in model_usage.values()
                if isinstance(item, dict)
            ),
            "cache_read_input_tokens": sum(
                int(item.get("cacheReadInputTokens") or 0)
                for item in model_usage.values()
                if isinstance(item, dict)
            ),
        }
    return {"cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}


def claude_metadata(data: dict[str, Any], spec: ModelSpec) -> dict[str, Any]:
    cache_summary = claude_cache_summary(data)
    return {
        "claude_model": spec.claude_model or spec.name,
        "claude_total_cost_usd": data.get("total_cost_usd"),
        "claude_usage": data.get("usage") if isinstance(data.get("usage"), dict) else {},
        "claude_model_usage": data.get("modelUsage") if isinstance(data.get("modelUsage"), dict) else {},
        "claude_cache_creation_input_tokens": cache_summary["cache_creation_input_tokens"],
        "claude_cache_read_input_tokens": cache_summary["cache_read_input_tokens"],
    }


def cursor_tokens_used(data: dict[str, Any]) -> int:
    usage = data.get("usage")
    if not isinstance(usage, dict):
        return 0
    return sum(
        int(usage.get(key) or 0)
        for key in ["inputTokens", "cacheWriteTokens", "cacheReadTokens", "outputTokens"]
    )


def antigravity_tokens_used(data: dict[str, Any]) -> int:
    """Return exact Antigravity usage without double-counting its total."""

    usage = data.get("usage")
    if not isinstance(usage, dict):
        return 0
    if usage.get("total_tokens") is not None:
        return int(usage.get("total_tokens") or 0)
    return sum(
        int(usage.get(key) or 0)
        for key in ["input_tokens", "output_tokens", "thinking_tokens", "cache_read_tokens"]
    )


def cursor_metadata(data: dict[str, Any], spec: ModelSpec) -> dict[str, Any]:
    usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
    return {
        "cursor_model": spec.cursor_model or spec.name,
        "runtime_model_reported": None,
        "runtime_model_verification": "provider_response_omits_model; exact_cli_id_required",
        "cursor_usage": usage,
        "cursor_cache_write_tokens": int(usage.get("cacheWriteTokens") or 0),
        "cursor_cache_read_tokens": int(usage.get("cacheReadTokens") or 0),
    }


def antigravity_model_id_from_label(label: str) -> str:
    for model_id, (expected, _display) in KNOWN_ANTIGRAVITY_MODELS.items():
        if expected == label:
            return model_id
    return safe_name(label).replace("_", "-")


def format_go_duration(seconds: int) -> str:
    return f"{int(seconds)}s"


def run_cmd(
    args: list[str],
    cwd: Path,
    stdin_text: str | None = None,
    timeout: int | None = None,
) -> subprocess.CompletedProcess[str]:
    process = subprocess.Popen(
        args,
        cwd=cwd,
        stdin=subprocess.PIPE if stdin_text is not None else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(input=stdin_text, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except (PermissionError, ProcessLookupError):
            try:
                process.kill()
            except (PermissionError, ProcessLookupError):
                pass
        try:
            stdout, stderr = process.communicate(timeout=2)
        except subprocess.TimeoutExpired:
            stdout = exc.stdout or ""
            stderr = exc.stderr or ""
        exc.stdout = stdout
        exc.stderr = stderr
        raise exc
    return subprocess.CompletedProcess(args, process.returncode, stdout, stderr)


def model_listing_command(spec: ModelSpec, executable: str) -> list[str] | None:
    """Return the provider's non-inference model-listing command, if any."""

    if spec.provider == "antigravity":
        return [executable, "models"]
    if spec.provider == "cursor":
        return [executable, "--list-models"]
    if spec.provider == "codex":
        return [executable, "debug", "models"]
    # Claude Code does not currently offer a stable, account-aware,
    # non-inference model-listing command. Its preflight verifies the binary
    # but deliberately does not pretend that proves access.
    return None


def _normalized_model_tokens(text: str) -> set[str]:
    """Extract conservative comparison tokens from a provider model listing."""

    return {
        match.lower()
        for match in re.findall(r"[A-Za-z0-9][A-Za-z0-9._-]*", text)
    }


def codex_supported_efforts(catalog_text: str, model_id: str) -> set[str] | None:
    """Return the reasoning levels advertised for one Codex model."""

    try:
        catalog = json.loads(catalog_text)
    except json.JSONDecodeError:
        return None
    models = catalog.get("models") if isinstance(catalog, dict) else None
    if not isinstance(models, list):
        return None
    for item in models:
        if not isinstance(item, dict) or item.get("slug") != model_id:
            continue
        levels = item.get("supported_reasoning_levels")
        if not isinstance(levels, list):
            return set()
        return {
            level["effort"]
            for level in levels
            if isinstance(level, dict) and isinstance(level.get("effort"), str)
        }
    return None


def preflight_model(spec: ModelSpec, cwd: Path, timeout: int = 15) -> dict[str, Any]:
    """Check a local CLI and, where supported, list models without inference.

    This is intentionally a read-only readiness check.  It never submits the
    benchmark prompt or asks a provider to generate an answer.  A successful
    executable check is distinct from confirmed model availability: providers
    without a model-listing command report ``model_available`` as ``None``.
    """

    binary_name = provider_binary(spec)
    executable = shutil.which(binary_name)
    requested_model = requested_provider_model(spec)
    result: dict[str, Any] = {
        "provider": spec.provider,
        "model": spec.name,
        "display_model": spec.display_name,
        "artifact_id": spec.artifact_id,
        "requested_provider_model": requested_model,
        "requested_effort": spec.reasoning_effort,
        "binary": binary_name,
        "executable": executable,
        "inference_attempted": False,
        "model_listing_supported": False,
        "model_available": None,
    }
    if not executable:
        return {
            **result,
            "state": "binary_missing",
            "returncode": 127,
            "stdout": "",
            "stderr": f"Required executable `{binary_name}` was not found on PATH.\n",
        }

    try:
        probe = run_cmd([executable, "--help"], cwd, timeout=timeout)
        probe_stdout = probe.stdout.encode("utf-8", errors="replace")
        probe_stderr = probe.stderr.encode("utf-8", errors="replace")
        result.update(
            {
                "state": "binary_ready" if probe.returncode == 0 else "binary_error",
                "returncode": probe.returncode,
                "probe_stdout_bytes": len(probe_stdout),
                "probe_stdout_sha256": hashlib.sha256(probe_stdout).hexdigest(),
                "probe_stderr_bytes": len(probe_stderr),
                "probe_stderr_sha256": hashlib.sha256(probe_stderr).hexdigest(),
            }
        )
    except subprocess.TimeoutExpired as exc:
        stdout, stderr, returncode = _timeout_result(exc, timeout)
        return {**result, "state": "binary_timeout", "returncode": returncode, "stdout": stdout, "stderr": stderr}

    if result["state"] != "binary_ready":
        return result

    if spec.provider == "antigravity" and not spec.antigravity_model:
        # `current` delegates selection to the user's CLI configuration, so a
        # listing cannot prove a particular model is available.
        return result

    listing_cmd = model_listing_command(spec, executable)
    if listing_cmd is None:
        return result

    provider_context = None
    if spec.provider == "codex":
        # Exercise the exact credential-file-free outer boundary used by live
        # calls, while requesting only Codex's model catalog.
        from benchbench_sandbox import isolated_provider_path

        provider_context = tempfile.TemporaryDirectory(prefix="benchbench-codex-preflight-")
        listing_cwd = Path(provider_context.name)
        listing_cmd = ["codex", *codex_broker_config_args(), "debug", "models"]
    else:
        listing_cwd = cwd

    result["model_listing_supported"] = True
    result["model_listing_command"] = listing_cmd
    try:
        if spec.provider == "codex":
            with isolated_provider_path("codex", listing_cwd):
                listing = run_cmd(listing_cmd, listing_cwd, timeout=timeout)
        else:
            listing = run_cmd(listing_cmd, listing_cwd, timeout=timeout)
        listing_text = f"{listing.stdout}\n{listing.stderr}"
        listing_tokens = _normalized_model_tokens(listing_text)
        known_label = spec.antigravity_expected_label or ""
        requested_candidates = {requested_model.lower(), spec.name.lower()}
        available = any(candidate and candidate in listing_tokens for candidate in requested_candidates)
        # Antigravity exposes friendly labels containing spaces and
        # punctuation as well as machine identifiers. Only the complete known
        # label may use textual matching; requested model IDs are always exact
        # catalog tokens so near-prefix typos cannot pass preflight.
        if known_label:
            available = available or known_label.lower() in listing_text.lower()
        stdout_bytes = listing.stdout.encode("utf-8", errors="replace")
        stderr_bytes = listing.stderr.encode("utf-8", errors="replace")
        result.update(
            {
                "model_listing_returncode": listing.returncode,
                "model_listing_stdout_bytes": len(stdout_bytes),
                "model_listing_stdout_sha256": hashlib.sha256(stdout_bytes).hexdigest(),
                "model_listing_stderr_bytes": len(stderr_bytes),
                "model_listing_stderr_sha256": hashlib.sha256(stderr_bytes).hexdigest(),
                "model_available": available if listing.returncode == 0 else None,
            }
        )
        if spec.provider == "codex" and spec.reasoning_effort and listing.returncode == 0:
            supported_efforts = codex_supported_efforts(listing.stdout, requested_model)
            result["supported_efforts"] = sorted(supported_efforts) if supported_efforts is not None else None
            result["effort_available"] = (
                spec.reasoning_effort in supported_efforts
                if supported_efforts is not None
                else None
            )
        if listing.returncode == 0 and not available:
            result["state"] = "model_unavailable"
        elif result.get("effort_available") is False:
            result["state"] = "reasoning_effort_unavailable"
        elif listing.returncode != 0:
            result["state"] = "model_listing_error"
    except subprocess.TimeoutExpired as exc:
        stdout, stderr, returncode = _timeout_result(exc, timeout)
        result.update(
            {
                "state": "model_listing_timeout",
                "model_listing_returncode": returncode,
                "model_listing_stdout": stdout,
                "model_listing_stderr": stderr,
            }
        )
    except (OSError, RuntimeError) as exc:
        result.update(
            {
                "state": "model_listing_error",
                "model_listing_returncode": 70,
                "model_listing_error": str(exc),
                "model_available": None,
            }
        )
    finally:
        if provider_context is not None:
            provider_context.cleanup()
    return result


def _timeout_result(exc: subprocess.TimeoutExpired, timeout: int) -> tuple[str, str, int]:
    stdout = exc.stdout or ""
    stderr = exc.stderr or ""
    if isinstance(stdout, bytes):
        stdout = stdout.decode("utf-8", errors="replace")
    if isinstance(stderr, bytes):
        stderr = stderr.decode("utf-8", errors="replace")
    stderr += f"\nTIMEOUT after {timeout} seconds\n"
    return stdout, stderr, -124


def _result_identity(spec: ModelSpec) -> dict[str, Any]:
    """Attach the immutable provider/model identity to every run record."""

    return {
        "model": spec.name,
        "display_model": spec.display_name,
        "provider": spec.provider,
        "artifact_id": spec.artifact_id,
        "requested_provider_model": requested_provider_model(spec),
    }


def codex_runtime_metadata(stderr: str, spec: ModelSpec, effort: str) -> dict[str, Any]:
    """Verify the runtime identity printed by Codex before every response."""

    model_matches = re.findall(r"(?m)^model:\s*(\S+)\s*$", stderr)
    effort_matches = re.findall(r"(?m)^reasoning effort:\s*(\S+)\s*$", stderr)
    actual_model = model_matches[-1] if model_matches else None
    actual_effort = effort_matches[-1] if effort_matches else None
    expected_model = spec.codex_model or spec.name
    return {
        "runtime_model_reported": actual_model,
        "runtime_effort_reported": actual_effort,
        "runtime_model_verification": "provider_reported",
        "model_mismatch": actual_model != expected_model or actual_effort != effort,
    }


def run_codex_model(spec: ModelSpec, prompt: str, out_path: Path, cwd: Path, effort: str, timeout: int) -> dict[str, Any]:
    prompt_path = out_path.with_suffix(".prompt.txt")
    prompt_path.write_text(prompt, encoding="utf-8")
    cmd = [
        "codex",
        "exec",
        "--skip-git-repo-check",
        "--ephemeral",
        "--ignore-user-config",
        "--sandbox",
        # Provider-native Seatbelt cannot be nested under the controller's
        # stricter gold-isolation profile. The outer profile is the actual OS
        # boundary; danger-full-access here prevents an incompatible second
        # sandbox, not unrestricted host execution.
        "danger-full-access",
        *codex_broker_config_args(),
        "-m",
        spec.codex_model or spec.name,
        "-c",
        f'model_reasoning_effort="{effort}"',
        "-c",
        "shell_environment_policy.inherit=none",
        "-c",
        'shell_environment_policy.exclude=["^BENCHBENCH_CODEX_BEARER_TOKEN$","^BENCHBENCH_CODEX_ACCOUNT_ID$"]',
        "--output-last-message",
        str(out_path),
        "-",
    ]
    try:
        completed = run_cmd(cmd, cwd, stdin_text=prompt, timeout=timeout)
        stdout = completed.stdout
        stderr = completed.stderr
        returncode = completed.returncode
    except subprocess.TimeoutExpired as exc:
        stdout, stderr, returncode = _timeout_result(exc, timeout)

    stdout_path = out_path.with_suffix(".stdout.txt")
    stderr_path = out_path.with_suffix(".stderr.txt")
    stdout_path.write_text(stdout, encoding="utf-8")
    stderr_path.write_text(stderr, encoding="utf-8")
    runtime = codex_runtime_metadata(stderr, spec, effort)
    if runtime["model_mismatch"] and returncode == 0:
        returncode = 65
    return {
        **_result_identity(spec),
        "returncode": returncode,
        "tokens_used": parse_tokens(stdout + "\n" + stderr),
        "out_path": str(out_path),
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "prompt_path": str(prompt_path),
        "sandbox_mode": "outer-seatbelt",
        "effort": effort,
        **runtime,
    }


def run_antigravity_model(
    spec: ModelSpec,
    prompt: str,
    out_path: Path,
    cwd: Path,
    effort: str,
    timeout: int,
) -> dict[str, Any]:
    prompt_path = out_path.with_suffix(".prompt.txt")
    stdout_path = out_path.with_suffix(".stdout.txt")
    stderr_path = out_path.with_suffix(".stderr.txt")
    log_path = out_path.with_suffix(".agy.log")
    prompt_path.write_text(prompt, encoding="utf-8")

    agy = shutil.which("agy")
    if not agy:
        message = "Antigravity CLI `agy` was not found on PATH.\n"
        out_path.write_text("", encoding="utf-8")
        stdout_path.write_text("", encoding="utf-8")
        stderr_path.write_text(message, encoding="utf-8")
        return {
            **_result_identity(spec),
            "returncode": 127,
            "tokens_used": 0,
            "out_path": str(out_path),
            "stdout_path": str(stdout_path),
            "stderr_path": str(stderr_path),
            "prompt_path": str(prompt_path),
            "antigravity_log_path": str(log_path),
            "antigravity_expected_label": spec.antigravity_expected_label,
            "antigravity_actual_label": None,
            "model_mismatch": bool(spec.antigravity_expected_label),
            "effort": effort,
        }

    cmd = [
        agy,
        "--print",
        prompt,
        "--output-format",
        "json",
        "--effort",
        effort if effort in {"low", "medium", "high"} else "high",
        "--sandbox",
        "--print-timeout",
        format_go_duration(timeout),
        "--log-file",
        str(log_path),
    ]
    if spec.antigravity_model:
        cmd.extend(["--model", spec.antigravity_model])
    try:
        completed = run_cmd(cmd, cwd, timeout=timeout + 30)
        stdout = completed.stdout
        stderr = completed.stderr
        returncode = completed.returncode
    except subprocess.TimeoutExpired as exc:
        stdout, stderr, returncode = _timeout_result(exc, timeout)

    stdout_path.write_text(stdout, encoding="utf-8")
    stderr_path.write_text(stderr, encoding="utf-8")
    data: dict[str, Any] = {}
    try:
        parsed = json.loads(stdout)
        if isinstance(parsed, dict):
            data = parsed
    except json.JSONDecodeError:
        data = {}
    result_text = data.get("response") if isinstance(data.get("response"), str) else stdout
    out_path.write_text(result_text, encoding="utf-8")
    log_text = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
    actual_label = parse_antigravity_selected_label(log_text)
    expected_label = spec.antigravity_expected_label
    model_mismatch = bool(expected_label and actual_label and actual_label != expected_label)
    if expected_label and not actual_label:
        model_mismatch = True
    permission_denied = (
        "headless mode cannot prompt for" in stderr
        and "auto-denied" in stderr
    )
    if permission_denied and returncode == 0:
        # Antigravity 1.1.9 reports a successful process even when its agent
        # produced no answer because a required tool was denied.  Preserve the
        # provider stderr but turn that false success into a typed failure.
        returncode = 77
    elif model_mismatch and returncode == 0:
        returncode = 86
        stderr += (
            "\nAntigravity selected-model mismatch: "
            f"expected {expected_label!r}, saw {actual_label!r}.\n"
        )
        stderr_path.write_text(stderr, encoding="utf-8")

    return {
        **_result_identity(spec),
        "returncode": returncode,
        "tokens_used": antigravity_tokens_used(data),
        "out_path": str(out_path),
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "prompt_path": str(prompt_path),
        "antigravity_log_path": str(log_path),
        "antigravity_expected_label": expected_label,
        "antigravity_actual_label": actual_label,
        "model_mismatch": model_mismatch,
        "antigravity_usage": data.get("usage") if isinstance(data.get("usage"), dict) else {},
        "permission_denied": permission_denied,
        "sandbox_mode": "nested-antigravity-plus-outer-seatbelt",
        "effort": effort,
    }


def run_claude_model(spec: ModelSpec, prompt: str, out_path: Path, cwd: Path, effort: str, timeout: int) -> dict[str, Any]:
    prompt_path = out_path.with_suffix(".prompt.txt")
    stdout_path = out_path.with_suffix(".stdout.txt")
    stderr_path = out_path.with_suffix(".stderr.txt")
    prompt_path.write_text(prompt, encoding="utf-8")

    claude = shutil.which("claude")
    if not claude:
        message = "Claude Code CLI `claude` was not found on PATH.\n"
        out_path.write_text("", encoding="utf-8")
        stdout_path.write_text("", encoding="utf-8")
        stderr_path.write_text(message, encoding="utf-8")
        return {
            **_result_identity(spec),
            "returncode": 127,
            "tokens_used": 0,
            "out_path": str(out_path),
            "stdout_path": str(stdout_path),
            "stderr_path": str(stderr_path),
            "prompt_path": str(prompt_path),
            "effort": effort,
        }

    max_budget_usd = os.getenv("BENCHBENCH_CLAUDE_MAX_BUDGET_USD", DEFAULT_CLAUDE_MAX_BUDGET_USD)
    cmd = [
        claude,
        "-p",
        "--model",
        spec.claude_model or spec.name,
        "--effort",
        effort if effort in {"low", "medium", "high", "xhigh", "max"} else "low",
        "--permission-mode",
        "default",
        "--output-format",
        "json",
        "--no-session-persistence",
        "--exclude-dynamic-system-prompt-sections",
        "--max-budget-usd",
        max_budget_usd,
    ]
    try:
        completed = run_cmd(cmd, cwd, stdin_text=prompt, timeout=timeout)
        stdout = completed.stdout
        stderr = completed.stderr
        returncode = completed.returncode
    except subprocess.TimeoutExpired as exc:
        stdout, stderr, returncode = _timeout_result(exc, timeout)

    stdout_path.write_text(stdout, encoding="utf-8")
    stderr_path.write_text(stderr, encoding="utf-8")
    data: dict[str, Any] = {}
    try:
        parsed = json.loads(stdout)
        if isinstance(parsed, dict):
            data = parsed
    except json.JSONDecodeError:
        data = {}

    result_text = data.get("result") if isinstance(data.get("result"), str) else stdout
    out_path.write_text(result_text, encoding="utf-8")
    if data.get("is_error") and returncode == 0:
        returncode = 1

    return {
        **_result_identity(spec),
        "returncode": returncode,
        "tokens_used": claude_tokens_used(data),
        "out_path": str(out_path),
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "prompt_path": str(prompt_path),
        "permission_mode": "default",
        "effort": effort,
        **claude_metadata(data, spec),
    }


def run_cursor_model(spec: ModelSpec, prompt: str, out_path: Path, cwd: Path, effort: str, timeout: int) -> dict[str, Any]:
    prompt_path = out_path.with_suffix(".prompt.txt")
    stdout_path = out_path.with_suffix(".stdout.txt")
    stderr_path = out_path.with_suffix(".stderr.txt")
    prompt_path.write_text(prompt, encoding="utf-8")

    cursor_agent = shutil.which("cursor-agent")
    if not cursor_agent:
        message = "Cursor Agent CLI `cursor-agent` was not found on PATH.\n"
        out_path.write_text("", encoding="utf-8")
        stdout_path.write_text("", encoding="utf-8")
        stderr_path.write_text(message, encoding="utf-8")
        return {
            **_result_identity(spec),
            "returncode": 127,
            "tokens_used": 0,
            "out_path": str(out_path),
            "stdout_path": str(stdout_path),
            "stderr_path": str(stderr_path),
            "prompt_path": str(prompt_path),
            "effort": effort,
        }

    cmd = [
        cursor_agent,
        "--print",
        "--output-format",
        "json",
        "--model",
        spec.cursor_model or spec.name,
        "--sandbox",
        "enabled",
        "--workspace",
        str(cwd),
        # This trusts only the controller-created disposable workspace. Tool
        # permissions remain enforced by Cursor's native sandbox and the
        # outer Seatbelt profile; this is not `--force`/`--yolo`.
        "--trust",
    ]
    try:
        completed = run_cmd(cmd, cwd, stdin_text=prompt, timeout=timeout)
        stdout = completed.stdout
        stderr = completed.stderr
        returncode = completed.returncode
    except subprocess.TimeoutExpired as exc:
        stdout, stderr, returncode = _timeout_result(exc, timeout)

    stdout_path.write_text(stdout, encoding="utf-8")
    stderr_path.write_text(stderr, encoding="utf-8")
    data: dict[str, Any] = {}
    try:
        parsed = json.loads(stdout)
        if isinstance(parsed, dict):
            data = parsed
    except json.JSONDecodeError:
        data = {}

    result_text = data.get("result") if isinstance(data.get("result"), str) else stdout
    out_path.write_text(result_text, encoding="utf-8")
    if data.get("is_error") and returncode == 0:
        returncode = 1

    return {
        **_result_identity(spec),
        "returncode": returncode,
        "tokens_used": cursor_tokens_used(data),
        "out_path": str(out_path),
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "prompt_path": str(prompt_path),
        "sandbox_mode": "nested-cursor-plus-outer-seatbelt",
        "effort": effort,
        **cursor_metadata(data, spec),
    }


def run_model(spec: ModelSpec, prompt: str, out_path: Path, cwd: Path, effort: str, timeout: int) -> dict[str, Any]:
    if spec.provider == "codex":
        return run_codex_model(spec, prompt, out_path, cwd, effort, timeout)
    if spec.provider == "antigravity":
        return run_antigravity_model(spec, prompt, out_path, cwd, effort, timeout)
    if spec.provider == "claude":
        return run_claude_model(spec, prompt, out_path, cwd, effort, timeout)
    if spec.provider == "cursor":
        return run_cursor_model(spec, prompt, out_path, cwd, effort, timeout)
    raise ValueError(f"Unsupported model provider: {spec.provider}")
