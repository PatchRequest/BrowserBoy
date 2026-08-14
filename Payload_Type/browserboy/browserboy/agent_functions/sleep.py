from mythic_container.MythicCommandBase import *
from mythic_container.MythicRPC import *


class SleepArguments(TaskArguments):
    def __init__(self, command_line, **kwargs):
        super().__init__(command_line, **kwargs)
        self.args = [
            CommandParameter(
                name="seconds",
                type=ParameterType.Number,
                description="Callback interval in seconds",
                parameter_group_info=[ParameterGroupInfo(required=True, ui_position=1)],
            ),
            CommandParameter(
                name="jitter",
                type=ParameterType.Number,
                description="Jitter percent",
                default_value=-1,
                parameter_group_info=[ParameterGroupInfo(required=False, ui_position=2)],
            ),
        ]

    async def parse_arguments(self):
        if not self.command_line:
            raise ValueError("sleep requires seconds")
        if self.command_line[0] != "{":
            pieces = self.command_line.split()
            self.add_arg("seconds", pieces[0])
            if len(pieces) > 1:
                self.add_arg("jitter", pieces[1])
        else:
            self.load_args_from_json_string(self.command_line)

    async def parse_dictionary(self, dictionary_arguments):
        self.load_args_from_dictionary(dictionary_arguments)


class SleepCommand(CommandBase):
    cmd = "sleep"
    needs_admin = False
    help_cmd = "sleep seconds [jitter]"
    description = "Set callback interval and jitter"
    version = 1
    author = "@PatchRequest"
    attackmapping = []
    argument_class = SleepArguments
    attributes = CommandAttributes(builtin=True, supported_os=[SupportedOS.Chrome])

    async def create_go_tasking(self, taskData: PTTaskMessageAllData) -> PTTaskCreateTaskingMessageResponse:
        seconds = taskData.args.get_arg("seconds")
        jitter = taskData.args.get_arg("jitter")
        display = f"{seconds}s"
        sleep_info = f"{seconds}s"
        if jitter is not None and int(jitter) >= 0:
            display += f" {jitter}%"
            sleep_info += f":{jitter}%"
        await SendMythicRPCCallbackUpdate(
            MythicRPCCallbackUpdateMessage(TaskID=taskData.Task.ID, SleepInfo=sleep_info)
        )
        return PTTaskCreateTaskingMessageResponse(
            TaskID=taskData.Task.ID,
            Success=True,
            DisplayParams=display,
        )

    async def process_response(self, task: PTTaskMessageAllData, response: any) -> PTTaskProcessResponseMessageResponse:
        return PTTaskProcessResponseMessageResponse(TaskID=task.Task.ID, Success=True)
