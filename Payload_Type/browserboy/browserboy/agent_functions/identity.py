from mythic_container.MythicCommandBase import *


class IdentityArguments(TaskArguments):
    def __init__(self, command_line, **kwargs):
        super().__init__(command_line, **kwargs)
        self.args = []

    async def parse_arguments(self):
        pass


class IdentityCommand(CommandBase):
    cmd = "identity"
    needs_admin = False
    help_cmd = "identity"
    description = "Return profile email, platform, and extension ID"
    version = 1
    author = "@PatchRequest"
    attackmapping = ["T1033"]
    argument_class = IdentityArguments
    attributes = CommandAttributes(builtin=True, supported_os=[SupportedOS.Chrome])

    async def create_go_tasking(self, taskData: PTTaskMessageAllData) -> PTTaskCreateTaskingMessageResponse:
        return PTTaskCreateTaskingMessageResponse(TaskID=taskData.Task.ID, Success=True)

    async def process_response(self, task: PTTaskMessageAllData, response: any) -> PTTaskProcessResponseMessageResponse:
        return PTTaskProcessResponseMessageResponse(TaskID=task.Task.ID, Success=True)
