import json
import tempfile
import unittest
import zipfile
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Payload_Type" / "browserboy"))

from browserboy.agent_functions.packaging import (  # noqa: E402
    KNOWN_COMMANDS,
    aespsk_mode,
    build_agent_config,
    parse_callback_host,
    stamp_extension,
    zip_extension,
)


class PackagingTests(unittest.TestCase):
    def test_parse_callback_host_scheme(self):
        host, ssl = parse_callback_host("https://mythic.example", False)
        self.assertEqual(host, "mythic.example")
        self.assertTrue(ssl)
        host, ssl = parse_callback_host("http://mythic", True)
        self.assertEqual(host, "mythic")
        self.assertFalse(ssl)
        host, ssl = parse_callback_host("mythic", False)
        self.assertEqual(host, "mythic")
        self.assertFalse(ssl)

    def test_aespsk_none(self):
        self.assertEqual(aespsk_mode(None), "none")
        self.assertEqual(aespsk_mode("none"), "none")
        self.assertEqual(aespsk_mode({"value": "none"}), "none")
        self.assertEqual(aespsk_mode({"value": "aes256_hmac"}), "aes256_hmac")

    def test_build_agent_config(self):
        config = build_agent_config(
            "uuid-1",
            {
                "callback_host": "http://mythic",
                "callback_port": "80",
                "get_uri": "index",
                "post_uri": "data",
                "query_path_name": "q",
                "headers": {"User-Agent": "test"},
                "callback_interval": "10",
                "callback_jitter": "5",
                "killdate": "2027-01-01",
                "AESPSK": {"value": "none"},
            },
            extension_name="lab",
        )
        self.assertEqual(config["callback_host"], "mythic")
        self.assertFalse(config["ssl"])
        self.assertEqual(config["get_uri"], "/index")
        self.assertEqual(config["post_uri"], "/data")
        self.assertEqual(config["aespsk"], "none")
        self.assertEqual(config["extension_name"], "lab")

    def test_stamp_and_zip(self):
        source = ROOT / "Payload_Type" / "browserboy" / "browserboy" / "agent_code" / "extension"
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "extension"
            stamp_extension(
                source,
                dest,
                config={"payload_uuid": "abc", "callback_host": "mythic"},
                manifest_fields={
                    "name": "lab-ext",
                    "description": "lab",
                    "version": "1.2.3",
                    "homepage_url": "https://example.test",
                    "update_url": "https://example.test/update.xml",
                },
                command_names=list(KNOWN_COMMANDS),
            )
            config_js = (dest / "lib" / "config.js").read_text(encoding="utf-8")
            self.assertIn('"payload_uuid": "abc"', config_js)
            self.assertNotIn("__BROWSERBOY_CONFIG__", config_js)
            commands_js = (dest / "lib" / "commands.js").read_text(encoding="utf-8")
            self.assertIn("import { run as tabs }", commands_js)
            self.assertIn("tabs,", commands_js)
            manifest = json.loads((dest / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["name"], "lab-ext")
            self.assertEqual(manifest["version"], "1.2.3")
            zip_path = Path(tmp) / "out.zip"
            zip_extension(dest, zip_path)
            with zipfile.ZipFile(zip_path) as archive:
                names = archive.namelist()
            self.assertIn("manifest.json", names)
            self.assertIn("service_worker.js", names)
            self.assertTrue(any(name.startswith("commands/") for name in names))


if __name__ == "__main__":
    unittest.main()
