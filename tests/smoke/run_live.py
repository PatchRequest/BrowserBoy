#!/usr/bin/env python3
"""Live smoke suite for every BrowserBoy command.

Start Chromium with the built extension. Talk to a real Mythic instance.
Fail the process if any case fails.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from mythic import mythic

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = Path(__file__).resolve().parent / "modules" / "smoke_hello.js"


def _env(name: str, default: str | None = None) -> str | None:
    value = os.environ.get(name)
    if value:
        return value
    return default


def parse_env_text(raw: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for line in raw.splitlines():
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        parsed[key.strip()] = value.strip().strip('"')
    return parsed


def load_mythic_secrets() -> tuple[str, str]:
    user = _env("MYTHIC_ADMIN_USER")
    password = _env("MYTHIC_ADMIN_PASSWORD")
    if user and password:
        return user, password

    env_file = _env("MYTHIC_ENV_FILE")
    if env_file:
        parsed = parse_env_text(Path(env_file).read_text(encoding="utf-8"))
        user = parsed.get("MYTHIC_ADMIN_USER")
        password = parsed.get("MYTHIC_ADMIN_PASSWORD")
        if user and password:
            return user, password

    ssh_target = _env("MYTHIC_SSH")
    remote_env = _env("MYTHIC_ENV_REMOTE")
    if ssh_target and remote_env:
        raw = subprocess.check_output(
            [
                "ssh",
                "-o",
                "BatchMode=yes",
                ssh_target,
                f"python3 -c \"from pathlib import Path; print(Path({remote_env!r}).read_text())\"",
            ],
            text=True,
        )
        parsed = parse_env_text(raw)
        user = parsed.get("MYTHIC_ADMIN_USER")
        password = parsed.get("MYTHIC_ADMIN_PASSWORD")
        if user and password:
            return user, password

    raise SystemExit(
        "Set MYTHIC_ADMIN_USER and MYTHIC_ADMIN_PASSWORD, or MYTHIC_ENV_FILE, "
        "or MYTHIC_SSH and MYTHIC_ENV_REMOTE"
    )


def decode_output(raw: Any) -> str:
    if raw is None:
        return ""
    if isinstance(raw, (bytes, bytearray)):
        raw = raw.decode("utf-8", errors="replace")
    text = str(raw)
    compact = "".join(text.split())
    if compact and all(ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=" for ch in compact):
        try:
            return base64.b64decode(text).decode("utf-8")
        except Exception:
            return text
    return text


def extract_task_text(blob: Any) -> str:
    if isinstance(blob, (bytes, bytearray)):
        return decode_output(blob)
    if isinstance(blob, list) and blob:
        first = blob[0]
        if isinstance(first, dict):
            return decode_output(first.get("response_text") or first.get("response") or "")
    if isinstance(blob, dict):
        return decode_output(blob.get("response_text") or blob.get("response") or "")
    return decode_output(blob)


def must_json(text: str) -> Any:
    return json.loads(text)


def must_contain(needle: str) -> Callable[[str], None]:
    def check(text: str) -> None:
        if needle not in text:
            raise AssertionError(f"missing {needle!r}")

    return check


def must_json_list() -> Callable[[str], None]:
    def check(text: str) -> None:
        data = must_json(text)
        if not isinstance(data, list):
            raise AssertionError("expected a JSON list")

    return check


@dataclass
class Case:
    name: str
    command: str
    params: dict[str, Any] | Callable[[dict[str, Any]], dict[str, Any]]
    check: Callable[[str], None]
    upload: Path | None = None
    capture: Callable[[str, dict[str, Any]], None] | None = None


@dataclass
class Result:
    name: str
    command: str
    ok: bool
    detail: str
    output: str = ""


def cases() -> list[Case]:
    def params_inject(ctx: dict[str, Any]) -> dict[str, Any]:
        if ctx.get("tab_id") is None:
            raise AssertionError("no tab_id from current")
        return {"tab_id": ctx["tab_id"], "javascript": "document.title"}

    def params_cookies(ctx: dict[str, Any]) -> dict[str, Any]:
        return {"action": "list", "url": ctx["smoke_url"]}

    def params_screenshot(ctx: dict[str, Any]) -> dict[str, Any]:
        params: dict[str, Any] = {"filename": "smoke.png"}
        if ctx.get("tab_id") is not None:
            params["tab_id"] = ctx["tab_id"]
        return params

    def params_close(ctx: dict[str, Any]) -> dict[str, Any]:
        if ctx.get("extra_tab_id") is None:
            raise AssertionError("no extra_tab_id")
        return {"action": "close", "tab_id": ctx["extra_tab_id"]}

    def params_update(ctx: dict[str, Any]) -> dict[str, Any]:
        if ctx.get("extra_tab_id") is None:
            raise AssertionError("no extra_tab_id")
        return {"action": "update", "tab_id": ctx["extra_tab_id"], "url": ctx["echo_url"]}

    def params_reload(ctx: dict[str, Any]) -> dict[str, Any]:
        if ctx.get("extra_tab_id") is None:
            raise AssertionError("no extra_tab_id")
        return {"action": "reload", "tab_id": ctx["extra_tab_id"]}

    def capture_current(text: str, ctx: dict[str, Any]) -> None:
        data = must_json(text)
        ctx["tab_id"] = data["id"]

    def capture_create(text: str, ctx: dict[str, Any]) -> None:
        data = must_json(text)
        ctx["extra_tab_id"] = data["id"]

    def check_current(text: str) -> None:
        data = must_json(text)
        if "id" not in data:
            raise AssertionError("current missing id")

    def check_identity(text: str) -> None:
        data = must_json(text)
        if "platform" not in data or "extension_id" not in data:
            raise AssertionError("identity missing platform or extension_id")

    def check_inject(text: str) -> None:
        data = must_json(text)
        blob = json.dumps(data)
        if "BrowserBoy Smoke" not in blob:
            raise AssertionError("inject did not return the smoke page title")

    def check_cookies(text: str) -> None:
        data = must_json(text)
        if not isinstance(data, list):
            raise AssertionError("cookies expected a list")
        names = {item.get("name") for item in data if isinstance(item, dict)}
        if "bb_smoke" not in names:
            raise AssertionError("cookie bb_smoke is missing")

    def check_request(text: str) -> None:
        data = must_json(text)
        if data.get("status") != 200:
            raise AssertionError(f"request status {data.get('status')}")
        if "smoke-ok" not in str(data.get("body", "")):
            raise AssertionError("request body missing smoke-ok")

    def check_screenshot(text: str) -> None:
        if "screenshot stored as" not in text:
            raise AssertionError("screenshot did not return a file id")

    def check_load(text: str) -> None:
        if "loaded smokehello" not in text:
            raise AssertionError("load did not register smokehello")

    def check_run_loaded(text: str) -> None:
        if not text.startswith("smoke-hello:"):
            raise AssertionError("run_loaded output is not smoke-hello")

    def check_history(text: str) -> None:
        must_json_list()(text)

    return [
        Case("identity", "identity", {}, check_identity),
        Case("current", "current", {}, check_current, capture=capture_current),
        Case("tabs_list", "tabs", {"action": "list"}, must_json_list()),
        Case("inject", "inject", params_inject, check_inject),
        Case("cookies", "cookies", params_cookies, check_cookies),
        Case("cookies_all", "cookies", {"action": "list"}, check_cookies),
        Case("history", "history", {"query": "127.0.0.1", "max_results": 20}, check_history),
        Case("bookmarks", "bookmarks", {"action": "list"}, must_json_list()),
        Case("downloads", "downloads", {"limit": 20}, must_json_list()),
        Case("clipboard_write", "clipboard", {"action": "write", "text": "SMOKE_CLIP"}, must_contain("wrote clipboard")),
        Case("clipboard_read", "clipboard", {"action": "read"}, must_contain("SMOKE_CLIP")),
        Case("request", "request", lambda ctx: {"method": "GET", "url": ctx["echo_url"]}, check_request),
        Case("screenshot", "screenshot", params_screenshot, check_screenshot),
        Case("tabs_create", "tabs", lambda ctx: {"action": "create", "url": ctx["smoke_url"], "active": False}, must_contain("id"), capture=capture_create),
        Case("tabs_update", "tabs", params_update, must_contain("id")),
        Case("tabs_reload", "tabs", params_reload, must_contain("reloaded")),
        Case("load", "load", {"name": "smokehello"}, check_load, upload=MODULE_PATH),
        Case("run_loaded", "run_loaded", {"name": "smokehello"}, check_run_loaded),
        Case("sleep", "sleep", {"seconds": 5, "jitter": 0}, must_contain("5s:0%")),
        Case("tabs_close", "tabs", params_close, must_contain("closed")),
        Case("exit", "exit", {}, must_contain("exited")),
    ]


async def newest_chrome_callback(client: Any, after_id: int) -> dict[str, Any] | None:
    callbacks = await mythic.get_all_callbacks(client)
    newest = None
    for item in callbacks:
        if not isinstance(item, dict):
            continue
        if str(item.get("user", "")).lower() != "chrome-user":
            continue
        if int(item.get("id") or 0) <= after_id:
            continue
        if newest is None or int(item["id"]) > int(newest["id"]):
            newest = item
    return newest


async def wait_for_callback(client: Any, after_id: int, timeout_s: float) -> dict[str, Any]:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        found = await newest_chrome_callback(client, after_id)
        if found:
            return found
        await asyncio.sleep(1)
    raise TimeoutError("no new chrome-user callback")


async def run_case(client: Any, callback_id: int, case: Case, ctx: dict[str, Any]) -> Result:
    try:
        params = case.params(ctx) if callable(case.params) else dict(case.params)
        file_ids = None
        if case.upload:
            file_id = await mythic.register_file(
                client,
                filename=case.upload.name,
                contents=case.upload.read_bytes(),
            )
            params["file"] = file_id
            file_ids = [file_id]
        task = await mythic.issue_task(
            mythic=client,
            command_name=case.command,
            parameters=params,
            callback_display_id=callback_id,
            file_ids=file_ids,
            wait_for_complete=True,
            timeout=40,
        )
        if not isinstance(task, dict):
            raise AssertionError(f"task result is {type(task)}")
        blob = await mythic.get_all_task_output_by_id(client, task["id"])
        output = extract_task_text(blob).strip()
        if task.get("status") != "success" or not task.get("completed"):
            raise AssertionError(output or f"task status={task.get('status')} completed={task.get('completed')}")
        case.check(output)
        if case.capture:
            case.capture(output, ctx)
        return Result(case.name, case.command, True, "ok", output)
    except Exception as exc:
        return Result(case.name, case.command, False, str(exc), locals().get("output", ""))


async def async_main(args: argparse.Namespace) -> int:
    user, password = load_mythic_secrets()
    extension = Path(args.extension).expanduser().resolve()
    if not (extension / "manifest.json").is_file():
        raise SystemExit(f"extension not found: {extension}")

    client = await mythic.login(
        server_ip=args.host,
        server_port=args.port,
        username=user,
        password=password,
        ssl=not args.no_ssl,
        timeout=30,
    )
    existing = await newest_chrome_callback(client, 0)
    after_id = int(existing["id"]) if existing else 0

    env = os.environ.copy()
    env["BROWSERBOY_EXTENSION"] = str(extension)
    env["BROWSERBOY_HOLD_MS"] = str(args.hold_ms)
    proc = subprocess.Popen(
        ["node", str(ROOT / "tests" / "smoke" / "hold_browser.mjs")],
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    assert proc.stdout is not None
    ready: dict[str, Any] | None = None
    deadline = time.time() + 30
    while time.time() < deadline:
        line = proc.stdout.readline()
        if not line and proc.poll() is not None:
            break
        if not line:
            time.sleep(0.1)
            continue
        line = line.strip()
        if line.startswith("{") and "ready" in line:
            ready = json.loads(line)
            break
    if not ready:
        proc.kill()
        raise SystemExit(f"browser holder failed to start: {proc.stdout.read() if proc.stdout else ''}")

    try:
        callback = await wait_for_callback(client, after_id, timeout_s=25)
        ctx = {
            "smoke_url": ready["smoke_url"],
            "echo_url": ready["echo_url"],
            "download_url": ready["download_url"],
            "callback_id": callback["id"],
        }
        results: list[Result] = []
        for case in cases():
            result = await run_case(client, int(callback["id"]), case, ctx)
            results.append(result)
            mark = "PASS" if result.ok else "FAIL"
            print(f"{mark}  {result.name:16}  {result.detail}")
            if not result.ok and args.fail_fast:
                break

        report = {
            "callback_id": callback["id"],
            "agent_callback_id": callback.get("agent_callback_id"),
            "smoke_url": ready["smoke_url"],
            "results": [result.__dict__ for result in results],
            "passed": sum(1 for result in results if result.ok),
            "failed": sum(1 for result in results if not result.ok),
            "total": len(results),
        }
        report_path = Path(args.report)
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"report {report_path}  {report['passed']}/{report['total']} passed")
        return 0 if report["failed"] == 0 else 1
    finally:
        proc.send_signal(15)
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Live BrowserBoy smoke suite")
    parser.add_argument("--host", default=_env("MYTHIC_HOST", "mythic"))
    parser.add_argument("--port", type=int, default=int(_env("MYTHIC_PORT", "7443")))
    parser.add_argument("--no-ssl", action="store_true")
    parser.add_argument(
        "--extension",
        default=_env("BROWSERBOY_EXTENSION", "/tmp/browserboy-lab"),
    )
    parser.add_argument("--hold-ms", type=int, default=180000)
    parser.add_argument("--report", default=str(ROOT / "tests" / "smoke" / "last_report.json"))
    parser.add_argument("--fail-fast", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    sys.exit(asyncio.run(async_main(parse_args())))
