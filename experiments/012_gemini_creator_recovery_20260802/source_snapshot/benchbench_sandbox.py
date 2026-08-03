"""Fail-closed execution boundaries for untrusted BenchBench artifacts.

The benchmark package is model-produced code.  It is never executed in the
repository checkout: every controller run gets a disposable copy and a macOS
Seatbelt profile that can read the Python runtime and its scratch tree only.
"""

from __future__ import annotations

import os
import json
import shutil
import subprocess
import sys
import tempfile
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable

from benchbench_model_backends import (
    CODEX_BROKER_ACCOUNT_ENV,
    CODEX_BROKER_TOKEN_ENV,
    run_cmd,
)


CURSOR_BROKER_TOKEN_ENV = "BENCHBENCH_CURSOR_BROKER_TOKEN"

# Antigravity's non-interactive mode cannot display approval prompts.  These
# action grants are intentionally broad only inside the controller-created
# disposable HOME/workspace; the outer Seatbelt profile remains the hard
# filesystem and process boundary.
ANTIGRAVITY_HEADLESS_COMMAND_PERMISSIONS = (
    "command(*)",
    # Antigravity's native macOS terminal sandbox cannot nest under the
    # controller's mandatory Seatbelt profile. This bypasses only that inner
    # layer; the outer profile remains the hard boundary for every command.
    "unsandboxed(*)",
)


class SandboxUnavailable(RuntimeError):
    """Raised rather than running untrusted code without an OS boundary."""


def _seatbelt_literal(path: Path) -> str:
    return str(path.resolve()).replace("\\", "\\\\").replace('"', '\\"')


def sandbox_exec_path() -> str:
    executable = shutil.which("sandbox-exec")
    if not executable:
        raise SandboxUnavailable("macOS sandbox-exec is required; refusing to execute untrusted benchmark code")
    return executable


def generated_code_profile(
    scratch: Path,
    *,
    network: bool = False,
    extra_reads: Iterable[Path] = (),
    allowed_executables: Iterable[Path] = (),
    extra_writes: Iterable[Path] = (),
    denied_executables: Iterable[Path] = (),
    denied_write_paths: Iterable[Path] = (),
    denied_write_subpaths: Iterable[Path] = (),
    mach_services: Iterable[str] = (),
    allow_user_preferences: bool = False,
    allow_system_sockets: bool = False,
    allow_subprocesses: bool = False,
) -> str:
    """Return a restrictive Seatbelt profile for generated package commands."""

    # `system.sb` supplies the narrow macOS runtime/locale rules.  Do not grant
    # `/private` wholesale: controller and solver scratch trees for concurrent
    # runs live there, and one run must not be able to inspect another.
    reads = [
        scratch,
        Path("/bin"),
        Path("/sbin"),
        Path("/usr"),
        Path("/System"),
        Path("/Library"),
        Path("/opt/homebrew"),
        Path("/private/var/select"),  # canonical target for /bin/sh on macOS
    ]
    reads.extend(extra_reads)
    clauses = [
        "(version 1)",
        "(deny default)",
        '(import "system.sb")',
        "(allow sysctl-read)",
        # KERN_PROCARGS2 can expose another same-user process's full
        # environment, including broker credentials; legacy KERN_PROCARGS does
        # the same. Keep ordinary runtime sysctls available to provider
        # binaries but deny both exact channels.
        '(deny sysctl-read (sysctl-name "kern.procargs"))',
        '(deny sysctl-read (sysctl-name "kern.procargs2"))',
    ]
    if allow_subprocesses:
        # Provider CLIs may fork/exec tools, but neither they nor those tools
        # need to inspect the controller's process table or parent environment.
        clauses.extend(["(allow process-fork)", "(allow process-exec)", "(allow signal (target self))"])
    else:
        clauses.extend(["(allow process-fork)", "(allow signal (target self))"])
        for executable in allowed_executables:
            clauses.append(
                f'(allow process-exec (literal "{_seatbelt_literal(executable)}"))'
            )
    for executable in denied_executables:
        clauses.append(f'(deny process-exec (literal "{_seatbelt_literal(executable)}"))')
    for service in mach_services:
        clauses.append(f'(allow mach-lookup (global-name "{service}"))')
    if allow_user_preferences:
        clauses.append("(allow user-preference-read)")
    if allow_system_sockets:
        clauses.append("(allow system-socket)")
    clauses.extend(
        [
            '(allow file-read-metadata (literal "/Users"))',
            '(allow file-read-metadata (literal "/opt"))',
            '(allow file-read-metadata (literal "/usr/local"))',
            f'(allow file-read-metadata (literal "{_seatbelt_literal(Path.home())}"))',
        ]
    )
    for path in extra_writes:
        clauses.append(f'(allow file-write* (subpath "{_seatbelt_literal(path)}"))')
    for path in denied_write_paths:
        clauses.append(f'(deny file-write* (literal "{_seatbelt_literal(path)}"))')
    for path in denied_write_subpaths:
        clauses.append(f'(deny file-write* (subpath "{_seatbelt_literal(path)}"))')
    for path in reads:
        for parent in reversed(path.resolve().parents):
            if parent == Path("/"):
                continue
            clauses.append(f'(allow file-read-metadata (literal "{_seatbelt_literal(parent)}"))')
        clauses.append(f'(allow file-read* (subpath "{_seatbelt_literal(path)}"))')
        clauses.append(f'(allow file-map-executable (subpath "{_seatbelt_literal(path)}"))')
    clauses.extend(
        [
            '(allow file-read* (literal "/dev/null"))',
            '(allow file-read* (literal "/dev/urandom"))',
            f'(allow file-write* (subpath "{_seatbelt_literal(scratch)}"))',
        ]
    )
    if network:
        clauses.append("(allow network*)")
    return "\n".join(clauses) + "\n"


def sandboxed_command(args: list[str], scratch: Path, *, network: bool = False, extra_reads: Iterable[Path] = ()) -> list[str]:
    """Wrap a command in a fail-closed Seatbelt invocation."""

    runtime_reads = list(extra_reads)
    executable = Path(args[0]).resolve()
    # Never add the filesystem root here: doing so would silently erase the
    # private-checkout boundary for /usr/bin/python3.
    runtime_reads.append(executable.parent)
    if executable == Path(sys.executable).resolve():
        # Virtual environments split their executable, standard library, and
        # site-packages across `base_prefix` and `prefix`.  Grant those runtime
        # trees explicitly instead of making the user's home directory readable.
        runtime_reads.extend([Path(sys.base_prefix).resolve(), Path(sys.prefix).resolve()])
    return [
        sandbox_exec_path(),
        "-p",
        generated_code_profile(
            scratch,
            network=network,
            extra_reads=runtime_reads,
            allowed_executables=[executable],
        ),
        *args,
    ]


def run_generated_command(args: list[str], scratch: Path, timeout: int) -> subprocess.CompletedProcess[str]:
    """Run model-generated Python within an isolated, networkless scratch tree."""

    # `run_cmd` deliberately inherits environment for provider CLIs.  Generated
    # code gets the opposite treatment: no credentials, tokens, proxy config,
    # or ambient HOME are passed across this boundary.
    previous = os.environ.copy()
    try:
        os.environ.clear()
        os.environ.update(sanitized_environment())
        return run_cmd(sandboxed_command(args, scratch), scratch, timeout=timeout)
    finally:
        os.environ.clear()
        os.environ.update(previous)



def sanitized_environment() -> dict[str, str]:
    """A minimal environment for invoking generated artifact code.

    `run_cmd` intentionally inherits its environment for provider CLIs.  This
    helper exists for callers that execute an artifact directly instead.
    """

    return {
        "PATH": os.defpath,
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "PYTHONDONTWRITEBYTECODE": "1",
    }


def sanitized_provider_environment(
    original: dict[str, str],
    *,
    binary: str,
    provider_home: Path,
    wrapper_root: Path,
    scratch_tmp: Path,
) -> dict[str, str]:
    """Keep provider process plumbing while dropping ambient credentials.

    Arbitrary API keys, cloud credentials, and application secrets from the
    controller environment must not be inherited by model-invoked tools.
    Codex receives one bearer token and account ID only in its trusted parent
    environment; its model-created tools inherit no environment variables.
    """

    safe_keys = {
        "USER",
        "LOGNAME",
        "SHELL",
        "LANG",
        "LC_ALL",
        "LC_CTYPE",
        "TERM",
        "COLORTERM",
        "NO_COLOR",
    }
    environment = {key: original[key] for key in safe_keys if key in original}
    environment["HOME"] = str(provider_home)
    if binary == "codex":
        environment["CODEX_HOME"] = str(provider_home / ".codex")
        token, account_id = load_codex_broker_credentials(original)
        environment[CODEX_BROKER_TOKEN_ENV] = token
        environment[CODEX_BROKER_ACCOUNT_ENV] = account_id
    elif binary == "cursor-agent":
        # Cursor's login consists of an access token and a refresh token in
        # macOS Keychain. Broker only the short-lived access token into the
        # trusted parent; Cursor's native sandbox scrubs model-created tools.
        environment[CURSOR_BROKER_TOKEN_ENV] = load_cursor_access_token()
        environment["CURSOR_CONFIG_DIR"] = str(provider_home / ".cursor")
        environment["CURSOR_DATA_DIR"] = str(provider_home / ".cursor-data")
        environment["CURSOR_AGENT_DISABLE_DEBUG_LOG"] = "1"
        environment["AGENT_CLI_CREDENTIAL_STORE"] = "memory"
    environment["PATH"] = f"{wrapper_root}{os.pathsep}{original.get('PATH', os.defpath)}"
    environment["TMPDIR"] = str(scratch_tmp)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return environment


def load_cursor_access_token() -> str:
    """Read only Cursor's access token from Keychain, never its refresh token."""

    try:
        completed = subprocess.run(
            [
                "/usr/bin/security",
                "find-generic-password",
                "-s",
                "cursor-access-token",
                "-a",
                "cursor-user",
                "-w",
            ],
            text=True,
            capture_output=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SandboxUnavailable("Cursor access-token broker failed") from exc
    token = completed.stdout.strip()
    if completed.returncode != 0 or not token or "\n" in token:
        raise SandboxUnavailable("Cursor login lacks a brokerable access token")
    return token


def antigravity_token_source(original: dict[str, str]) -> Path:
    """Resolve the one authorized Antigravity login file without broad config."""

    original_home = Path(original.get("HOME", str(Path.home())))
    source = original_home / ".gemini" / "antigravity-cli" / "antigravity-oauth-token"
    if not source.is_file() or source.is_symlink():
        raise SandboxUnavailable("A regular Antigravity OAuth token file is required")
    return source


def _stage_antigravity_token_once(original: dict[str, str], provider_home: Path) -> threading.Thread:
    """Serve Antigravity auth once through a FIFO, then remove the pathname.

    The provider can load its session during startup, but a later model-created
    tool cannot reopen a copied credential because no credential file exists.
    """

    try:
        token = antigravity_token_source(original).read_bytes()
    except OSError as exc:
        raise SandboxUnavailable("Antigravity OAuth token could not be read safely") from exc
    if not token:
        raise SandboxUnavailable("Antigravity OAuth token is empty")
    token_dir = provider_home / ".gemini" / "antigravity-cli"
    token_dir.mkdir(parents=True, mode=0o700, exist_ok=True)
    fifo = token_dir / "antigravity-oauth-token"
    os.mkfifo(fifo, mode=0o600)

    def serve() -> None:
        try:
            with fifo.open("wb", buffering=0) as handle:
                handle.write(token)
        finally:
            try:
                fifo.unlink()
            except FileNotFoundError:
                pass

    thread = threading.Thread(target=serve, name="benchbench-antigravity-auth", daemon=True)
    thread.start()
    return thread


def antigravity_headless_permissions(scratch: Path) -> tuple[str, ...]:
    """Return the file-scoped rules plus sandboxed command approval."""

    workspace = scratch.resolve()
    return (
        f"read_file({workspace})",
        f"write_file({workspace})",
        *ANTIGRAVITY_HEADLESS_COMMAND_PERMISSIONS,
    )


def _write_antigravity_headless_settings(provider_home: Path, scratch: Path) -> Path:
    """Create a disposable, non-interactive permission policy for Antigravity.

    The global user settings are deliberately not copied.  Antigravity's
    permission matcher maps directory listing to ``read_file``; file mutation
    and terminal execution have their own action names.  The outer Seatbelt
    profile still limits every allowed action to the disposable run tree.
    """

    settings_dir = provider_home / ".gemini" / "antigravity-cli"
    settings_dir.mkdir(parents=True, mode=0o700)
    settings_path = settings_dir / "settings.json"
    settings_path.write_text(
        json.dumps(
            {
                "permissions": {
                    "allow": list(antigravity_headless_permissions(scratch)),
                    # The CLI needs its disposable settings and startup token,
                    # but model-created file tools never need provider state.
                    "deny": [f"read_file({provider_home.resolve()})"],
                    "ask": [],
                },
                "allowNonWorkspaceAccess": False,
                "artifactReviewPolicy": "always-proceed",
                # Headless mode cannot surface the AskPermission meta-tool.
                # The outer Seatbelt profile still rejects out-of-scope I/O.
                "toolPermission": "always-proceed",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    settings_path.chmod(0o600)
    return settings_path


def load_codex_broker_credentials(original: dict[str, str]) -> tuple[str, str]:
    """Load a bounded ChatGPT session without copying any credential file."""

    explicit_token = original.get(CODEX_BROKER_TOKEN_ENV)
    explicit_account = original.get(CODEX_BROKER_ACCOUNT_ENV)
    if explicit_token or explicit_account:
        if not explicit_token or not explicit_account:
            raise SandboxUnavailable(
                f"{CODEX_BROKER_TOKEN_ENV} and {CODEX_BROKER_ACCOUNT_ENV} must be set together"
            )
        return explicit_token, explicit_account
    original_home = Path(original.get("HOME", str(Path.home())))
    source_home = Path(original.get("CODEX_HOME", original_home / ".codex"))
    auth_source = source_home / "auth.json"
    if not auth_source.is_file() or auth_source.is_symlink():
        raise SandboxUnavailable("A regular Codex auth.json is required for the credential broker")
    try:
        auth = json.loads(auth_source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SandboxUnavailable("Codex auth.json could not be read safely") from exc
    tokens = auth.get("tokens")
    token = tokens.get("access_token") if isinstance(tokens, dict) else None
    account_id = tokens.get("account_id") if isinstance(tokens, dict) else None
    if not isinstance(token, str) or not token or not isinstance(account_id, str) or not account_id:
        raise SandboxUnavailable("Codex login lacks an access token or account ID")
    return token, account_id


@contextmanager
def isolated_provider_path(binary: str, scratch: Path):
    """Put a Seatbelt-wrapped provider binary first on PATH for one model call.

    Provider authentication is deliberately limited to known configuration
    roots; the checkout, its parent, and every private gold file remain outside
    the profile.  The provider still has network access and can write only to
    its disposable solver bundle.
    """

    if binary == "claude":
        raise SandboxUnavailable(
            f"Live provider boundary for `{binary}` is not audited; refusing execution"
        )
    actual = shutil.which(binary)
    if not actual:
        raise SandboxUnavailable(f"Required provider executable `{binary}` was not found")
    resolved_actual = Path(actual).resolve()
    extra_reads = [
        Path(actual).parent,
        resolved_actual.parent,
        Path("/usr/local"),
        Path("/opt/homebrew"),
        # Networked provider CLIs need the macOS TLS trust bundle and OpenSSL
        # configuration.  `/etc/ssl` resolves into this narrow system-owned
        # directory; without it HTTPS fails inside Seatbelt before inference.
        Path("/private/etc/ssl"),
    ]
    if binary == "cursor-agent":
        # The PATH entry is a small launcher whose Node runtime and bundled
        # sandbox live in this versioned, read-only installation tree.
        extra_reads.append(Path.home() / ".local" / "share" / "cursor-agent")
    # Cursor falls back to a shared `/tmp/.cursor` store when its data path is
    # longer than 84 characters. Keep this audited wrapper root short so every
    # call retains a unique, outer-sandboxed store instead.
    with tempfile.TemporaryDirectory(prefix="bbp-", dir="/tmp") as wrapper_name:
        wrapper_root = Path(wrapper_name).resolve()
        previous = os.environ.copy()
        provider_home = wrapper_root / "home"
        provider_home.mkdir()
        if binary == "codex":
            (provider_home / ".codex").mkdir()
        elif binary == "cursor-agent":
            (provider_home / ".cursor").mkdir()
            (provider_home / ".cursor-data").mkdir()
        elif binary == "agy":
            _write_antigravity_headless_settings(provider_home, scratch)
        antigravity_auth_thread = (
            _stage_antigravity_token_once(previous, provider_home)
            if binary == "agy"
            else None
        )
        wrapper_bin = wrapper_root / binary
        profile = generated_code_profile(
            scratch,
            network=True,
            extra_reads=[wrapper_root, *extra_reads],
            allow_subprocesses=True,
            extra_writes=[wrapper_root],
            denied_write_paths=(
                [provider_home / ".gemini" / "antigravity-cli" / "antigravity-oauth-token"]
                if binary == "agy"
                else []
            ),
            # Credentials are brokered before the provider enters Seatbelt.
            # Provider processes retain the narrow Security.framework services
            # needed for TLS trust, but model-created tools must never be able
            # to invoke the Keychain command-line client.
            denied_executables=[Path("/usr/bin/security")],
            mach_services=(
                [
                    "com.apple.SystemConfiguration.DNSConfiguration",
                    "com.apple.SecurityServer",
                    "com.apple.securityd.xpc",
                ]
                if binary == "cursor-agent"
                else [
                    # Codex's Rust HTTP stack asks SystemConfiguration for the
                    # active network path and Security.framework for TLS trust.
                    # Without these exact lookups, Seatbelt permits sockets but
                    # every HTTPS stream disconnects before a response arrives.
                    "com.apple.SystemConfiguration.configd",
                    "com.apple.SystemConfiguration.DNSConfiguration",
                    "com.apple.SecurityServer",
                    "com.apple.securityd.xpc",
                ]
                if binary == "codex"
                else []
            ),
            allow_user_preferences=binary == "cursor-agent",
            allow_system_sockets=binary in {"codex", "cursor-agent"},
        )
        escaped_profile = profile.replace("'", "'\\\"'\\\"'")
        escaped_actual = actual.replace("'", "'\\\"'\\\"'")
        if binary == "cursor-agent":
            # Cursor natively accepts CURSOR_AUTH_TOKEN. Keep the credential
            # out of argv so ordinary host process listings cannot print it.
            # The inner sandbox removes it from model-created tool processes.
            wrapper_text = (
                "#!/bin/sh\n"
                f'token="${{{CURSOR_BROKER_TOKEN_ENV}:?missing Cursor broker token}}"\n'
                f"unset {CURSOR_BROKER_TOKEN_ENV}\n"
                "export CURSOR_AUTH_TOKEN=\"$token\"\n"
                "unset token\n"
                f"exec /usr/bin/sandbox-exec -p '{escaped_profile}' '{escaped_actual}' \"$@\"\n"
            )
        else:
            wrapper_text = (
                "#!/bin/sh\n"
                f"exec /usr/bin/sandbox-exec -p '{escaped_profile}' '{escaped_actual}' \"$@\"\n"
            )
        wrapper_bin.write_text(wrapper_text, encoding="utf-8")
        wrapper_bin.chmod(0o700)
        scratch_tmp = (scratch / ".provider-tmp").resolve()
        scratch_tmp.mkdir(exist_ok=True)
        os.environ.clear()
        os.environ.update(
            sanitized_provider_environment(
                previous,
                binary=binary,
                provider_home=provider_home,
                wrapper_root=wrapper_root,
                scratch_tmp=scratch_tmp,
            )
        )
        try:
            yield
        finally:
            os.environ.clear()
            os.environ.update(previous)
            if antigravity_auth_thread is not None:
                antigravity_auth_thread.join(timeout=2)
