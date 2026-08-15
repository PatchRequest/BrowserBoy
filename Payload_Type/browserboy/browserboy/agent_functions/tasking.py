"""Create Mythic tasking that uses the hardcoded wire name."""

from mythic_container.MythicCommandBase import PTTaskCreateTaskingMessageResponse

from .aliases import canonical_command_from_task, command_alias


def wired_tasking(task_data, display: str = "") -> PTTaskCreateTaskingMessageResponse:
    return PTTaskCreateTaskingMessageResponse(
        TaskID=task_data.Task.ID,
        Success=True,
        CommandName=command_alias(canonical_command_from_task(task_data)),
        DisplayParams=display,
    )
