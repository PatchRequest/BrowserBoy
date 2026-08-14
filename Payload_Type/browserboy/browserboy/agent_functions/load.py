from mythic_container.MythicCommandBase import *
from mythic_container.MythicRPC import *


class LoadArguments(TaskArguments):
    def __init__(self, command_line, **kwargs):
        super().__init__(command_line, **kwargs)
        self.args = [
            CommandParameter(
                name="name",
                type=ParameterType.String,
                description="Command name to register. Must be a JS identifier.",
                parameter_group_info=[ParameterGroupInfo(required=True, ui_position=1)],
            ),
            CommandParameter(
                name="file",
                type=ParameterType.File,
                description="JS module that exports async function run(task, ctx)",
                parameter_group_info=[ParameterGroupInfo(required=True, ui_position=2)],
            ),
        ]

    async def parse_arguments(self):
        if not self.command_line:
            raise ValueError("load requires name and file")
        if self.command_line[0] != "{":
            raise ValueError("load requires named arguments or the modal")
        self.load_args_from_json_string(self.command_line)

    async def parse_dictionary(self, dictionary_arguments):
        self.load_args_from_dictionary(dictionary_arguments)


class LoadCommand(CommandBase):
    cmd = "load"
    needs_admin = False
    help_cmd = "load -name foo -file module.js"
    description = "Download a JS module and register it for sandbox execution"
    version = 1
    author = "@PatchRequest"
    attackmapping = ["T1129"]
    argument_class = LoadArguments
    attributes = CommandAttributes(builtin=True, supported_os=[SupportedOS.Chrome])

    async def create_go_tasking(self, taskData: PTTaskMessageAllData) -> PTTaskCreateTaskingMessageResponse:
        name = taskData.args.get_arg("name")
        file_arg = taskData.args.get_arg("file")
        search = await SendMythicRPCFileSearch(
            MythicRPCFileSearchMessage(TaskID=taskData.Task.ID, AgentFileID=file_arg)
        )
        if not search.Success or not search.Files:
            raise Exception(f"failed to find uploaded file: {search.Error}")
        taskData.args.add_arg("file_id", search.Files[0].AgentFileId)
        taskData.args.remove_arg("file")
        return PTTaskCreateTaskingMessageResponse(
            TaskID=taskData.Task.ID,
            Success=True,
            DisplayParams=name,
        )

    async def process_response(self, task: PTTaskMessageAllData, response: any) -> PTTaskProcessResponseMessageResponse:
        return PTTaskProcessResponseMessageResponse(TaskID=task.Task.ID, Success=True)
