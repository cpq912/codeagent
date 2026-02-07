from typing import List, Optional
from pydantic import BaseModel, Field
from codeagent.tools.registry import tool
from codeagent.core.context import current_task_manager
from codeagent.core.task_manager import TaskStatus

class TaskItem(BaseModel):
    id: str = Field(..., description="Unique ID for the task")
    description: str = Field(..., description="Description of the task")
    dependencies: List[str] = Field(default_factory=list, description="IDs of tasks that must be completed first")

class PlanTaskArgs(BaseModel):
    tasks: List[TaskItem] = Field(..., description="List of tasks to create the plan")

class UpdateTaskArgs(BaseModel):
    task_id: str = Field(..., description="ID of the task to update")
    status: TaskStatus = Field(..., description="New status of the task")
    result: Optional[str] = Field(None, description="Summary of the result")
    error: Optional[str] = Field(None, description="Error message if failed")

@tool
def plan_task(args: PlanTaskArgs) -> str:
    """
    Create or overwrite the current task plan.
    Only available in Plan Mode.
    """
    tm = current_task_manager.get()
    if not tm:
        return "Error: Plan Mode is not active or TaskManager is not initialized."
    
    # Convert args to dicts for TaskManager
    tasks_data = [t.model_dump() for t in args.tasks]
    tm.create_plan(tasks_data)
    
    return "Plan created successfully.\n" + tm.get_plan_summary()

@tool
def update_task_status(args: UpdateTaskArgs) -> str:
    """
    Update the status of a specific task.
    Use this to mark tasks as completed or failed, or to record results.
    """
    tm = current_task_manager.get()
    if not tm:
        return "Error: Plan Mode is not active."
    
    try:
        tm.update_task(
            task_id=args.task_id,
            status=args.status,
            result=args.result,
            error=args.error
        )
        return f"Task {args.task_id} updated to {args.status}.\n" + tm.get_plan_summary()
    except ValueError as e:
        return f"Error updating task: {str(e)}"
