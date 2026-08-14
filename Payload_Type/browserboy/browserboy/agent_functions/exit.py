from mythic_container.MythicCommandBase import *


class ExitArguments(TaskArguments):
    def __init__(self, command_line, **kwargs):
        super().__init__(command_line, **kwargs)
        self.args = []

    async def parse_arguments(self):
        pass


class ExitCommand(CommandBase):
    cmd = "exit"
    needs_admin = False
    help_cmd = "exit"
    description = "Stop alarms and mark the agent dead"
    version = 1
    author = "@PatchRequest"
    attackmapping = []
    argument_class = ExitArguments
    supported_ui_features = ["callback_table:exit"]
    is_exit = True
    attributes = CommandAttributes(builtin=True, supported_os=[SupportedOS.Chrome])

    async def create_go_tasking(self, taskData: PTTaskMessageAllData) -> PTTaskCreateTaskingMessageResponse:
        return PTTaskCreateTaskingMessageResponse(TaskID=taskData.Task.ID, Success=True)

    async def process_response(self, task: PTTaskMessageAllData, response: any) -> PTTaskProcessResponseMessageResponse:
        return PTTaskProcessResponseMessageResponse(TaskID=task.Task.ID, Success=True)
