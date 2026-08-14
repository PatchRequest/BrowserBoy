import pathlib
import tempfile
from mythic_container.MythicCommandBase import *
from mythic_container.MythicRPC import *
from mythic_container.PayloadBuilder import *

from .packaging import (
    KNOWN_COMMANDS,
    aespsk_mode,
    build_agent_config,
    stamp_extension,
    zip_extension,
)


class Browserboy(PayloadType):
    name = "browserboy"
    file_extension = "zip"
    author = "@PatchRequest"
    supported_os = [SupportedOS.Chrome]
    wrapper = False
    wrapped_payloads = []
    note = "Manifest V3 Chrome extension. HTTP C2. Lab build uses AESPSK=none."
    supports_dynamic_loading = True
    mythic_encrypts = True
    translation_container = None
    semver = "0.1.0"
    c2_profiles = ["http"]
    c2_parameter_deviations = {
        "http": {
            "encrypted_exchange_check": C2ParameterDeviation(supported=False),
        }
    }
    build_parameters = [
        BuildParameter(
            name="name",
            parameter_type=BuildParameterType.String,
            description="Chrome extension name",
            default_value="browserboy",
        ),
        BuildParameter(
            name="description",
            parameter_type=BuildParameterType.String,
            description="Chrome extension description",
            default_value="Browser helper",
        ),
        BuildParameter(
            name="version",
            parameter_type=BuildParameterType.String,
            description="Chrome extension version",
            default_value="1.0.0",
        ),
        BuildParameter(
            name="homepage_url",
            parameter_type=BuildParameterType.String,
            description="homepage_url in the manifest",
            default_value="https://example.com",
        ),
        BuildParameter(
            name="update_url",
            parameter_type=BuildParameterType.String,
            description="update_url in the manifest",
            default_value="https://example.com/update.xml",
        ),
    ]
    agent_path = pathlib.Path(".") / "browserboy"
    agent_icon_path = agent_path / "agent_functions" / "browserboy.svg"
    agent_code_path = agent_path / "agent_code"
    build_steps = [
        BuildStep(step_name="Gathering Files", step_description="Copy extension sources"),
        BuildStep(step_name="Validating C2", step_description="Require HTTP with AESPSK=none"),
        BuildStep(step_name="Stamping", step_description="Write config, manifest, and command registry"),
        BuildStep(step_name="Packaging", step_description="Zip the unpacked extension"),
    ]

    async def _step(self, name: str, ok: bool, stdout: str = "", stderr: str = "") -> None:
        await SendMythicRPCPayloadUpdatebuildStep(
            MythicRPCPayloadUpdateBuildStepMessage(
                PayloadUUID=self.uuid,
                StepName=name,
                StepStdout=stdout,
                StepStderr=stderr,
                StepSuccess=ok,
            )
        )

    async def build(self) -> BuildResponse:
        resp = BuildResponse(status=BuildStatus.Error)
        try:
            selected = list(self.commands.get_commands())
            if not selected:
                selected = list(KNOWN_COMMANDS)

            source = pathlib.Path(self.agent_code_path) / "extension"
            if not source.is_dir():
                resp.build_stderr = f"missing extension sources at {source}"
                return resp
            await self._step("Gathering Files", True, f"source={source}\ncommands={selected}")

            http_c2 = None
            for c2 in self.c2info:
                if c2.get_c2profile().get("name") == "http":
                    http_c2 = c2
                    break
            if http_c2 is None:
                await self._step("Validating C2", False, "", "http C2 profile is required")
                resp.build_stderr = "browserboy requires the http C2 profile"
                return resp

            params = http_c2.get_parameters_dict()
            mode = aespsk_mode(params.get("AESPSK", "none"))
            if mode != "none":
                await self._step(
                    "Validating C2",
                    False,
                    "",
                    f"AESPSK={mode} is not supported in v1. Set AESPSK to none.",
                )
                resp.build_stderr = "browserboy v1 supports AESPSK=none only"
                return resp

            exchange = params.get("encrypted_exchange_check", False)
            if exchange in (True, "T", "true", "True"):
                await self._step(
                    "Validating C2",
                    False,
                    "",
                    "encrypted_exchange_check is not supported",
                )
                resp.build_stderr = "encrypted_exchange_check is not supported"
                return resp
            await self._step("Validating C2", True, "http AESPSK=none")

            extension_name = self.get_parameter("name")
            config = build_agent_config(
                self.uuid,
                params,
                extension_name=extension_name,
            )
            manifest_fields = {
                "name": extension_name,
                "description": self.get_parameter("description"),
                "version": self.get_parameter("version"),
                "homepage_url": self.get_parameter("homepage_url"),
                "update_url": self.get_parameter("update_url"),
            }

            with tempfile.TemporaryDirectory(prefix="browserboy-") as tmp:
                dest = pathlib.Path(tmp) / "extension"
                stamp_extension(
                    source,
                    dest,
                    config=config,
                    manifest_fields=manifest_fields,
                    command_names=selected,
                )
                await self._step("Stamping", True, f"host={config['callback_host']}:{config['callback_port']}")

                zip_path = pathlib.Path(tmp) / "browserboy.zip"
                zip_extension(dest, zip_path)
                resp.payload = zip_path.read_bytes()

            await self._step("Packaging", True, f"bytes={len(resp.payload)}")
            resp.status = BuildStatus.Success
            resp.build_message = "built unpacked Chrome extension zip"
            return resp
        except Exception as exc:
            resp.build_stderr = f"Error building payload: {exc}"
            return resp
