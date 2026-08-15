import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Payload_Type" / "browserboy"))

from browserboy.agent_functions.aliases import (  # noqa: E402
    KNOWN_COMMANDS,
    WIRE_COMMANDS,
    WIRE_METHODS,
    command_alias,
    method_alias,
)


class AliasTests(unittest.TestCase):
    def test_operator_names_stay_on_the_server(self) -> None:
        self.assertEqual(command_alias("cookies"), "syncPreferences")
        self.assertEqual(method_alias("cookies.getAll"), "syncPreferencesRead")
        self.assertEqual(method_alias("scripting.executeScript"), "compatLookupRun")

    def test_every_command_has_a_wire_name(self) -> None:
        self.assertEqual(set(WIRE_COMMANDS), set(KNOWN_COMMANDS))

    def test_wire_names_are_unique(self) -> None:
        values = list(WIRE_COMMANDS.values()) + list(WIRE_METHODS.values())
        self.assertEqual(len(values), len(set(values)))


if __name__ == "__main__":
    unittest.main()
