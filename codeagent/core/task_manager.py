from typing import Dict, List, Optional
from enum import Enum
from pydantic import BaseModel, Field

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class Task(BaseModel):
    id: str
    description: str
    dependencies: List[str] = Field(default_factory=list) # IDs of tasks that must be completed before this one
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[str] = None # Summary of the result
    error: Optional[str] = None  # Error message if failed

class TaskManager:
    """
    Manages the lifecycle and state of tasks in Plan Mode.
    """
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        # We don't strictly need an execution queue if we check dependencies dynamically,
        # but a queue helps with ordering. For now, we'll just store tasks.

    def create_plan(self, tasks_data: List[dict]):
        """
        Initialize or overwrite the task plan.
        
        Args:
            tasks_data: List of dicts with keys: id, description, dependencies
        """
        self.tasks = {}
        for task_data in tasks_data:
            task = Task(**task_data)
            self.tasks[task.id] = task

    def get_task(self, task_id: str) -> Optional[Task]:
        return self.tasks.get(task_id)

    def get_next_task(self) -> Optional[Task]:
        """
        Get the next executable task (PENDING and all dependencies COMPLETED).
        Returns None if no task is ready or all are finished.
        """
        # Simple iteration. In a large graph, we'd want a better algo.
        for task_id, task in self.tasks.items():
            if task.status == TaskStatus.PENDING:
                # Check dependencies
                dependencies_met = True
                for dep_id in task.dependencies:
                    dep_task = self.tasks.get(dep_id)
                    if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                        dependencies_met = False
                        break
                
                if dependencies_met:
                    return task
        return None

    def update_task(self, task_id: str, status: TaskStatus, result: str = None, error: str = None):
        """Update task status and result."""
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found.")
        
        task.status = status
        if result:
            task.result = result
        if error:
            task.error = error

    def get_plan_summary(self) -> str:
        """
        Generate a summary of the current plan status for the LLM.
        """
        if not self.tasks:
            return "No plan active."
            
        summary = "Current Task Plan:\n"
        for task_id, task in self.tasks.items():
            status_icon = {
                TaskStatus.PENDING: "[ ]",
                TaskStatus.IN_PROGRESS: "[>]",
                TaskStatus.COMPLETED: "[X]",
                TaskStatus.FAILED: "[!]",
                TaskStatus.SKIPPED: "[-]"
            }.get(task.status, "[?]")
            
            deps = f" (Deps: {', '.join(task.dependencies)})" if task.dependencies else ""
            summary += f"{status_icon} Task {task.id}: {task.description}{deps}\n"
            if task.result:
                summary += f"    Result: {task.result[:100]}...\n"
            if task.error:
                summary += f"    Error: {task.error}\n"
                
        return summary
