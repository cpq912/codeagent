from contextvars import ContextVar
from typing import Any

# Context variable to hold the TaskManager instance for the current execution context
# This allows tools to access the TaskManager without direct reference to the Agent
current_task_manager = ContextVar("current_task_manager", default=None)
