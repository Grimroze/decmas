"""
Manages the dependencies and asynchronous dispatch of tasks.
"""
from typing import List, Optional, Set
from .models import Task
import threading

class TaskQueue:
    """
    A dynamic queue that holds pending tasks and manages their dependencies.
    Agents asynchronously claim ready tasks from this queue.
    """
    def __init__(self):
        self.pending_tasks = []

        # maintain a set of completed task ids cuz it's faster to search in here
        self.completed_task_ids : Set[int] = set()

        # threading lock so multiple agents don't clash for the same task in the queue
        self.lock = threading.Lock()

    def add_task(self, task: Task) -> None:
        """Adds a new task to the queue."""
        with self.lock:
            self.pending_tasks.append(task)

    def add_tasks(self, tasks: List[Task]) -> None:
        """Adds multiple tasks to the queue."""
        with self.lock:
            self.pending_tasks.extend(tasks)

    def get_ready_task(self) -> Optional[Task]:
        """
        Returns a task whose dependencies have all been completed.
        Returns None if no task is ready (all blocked or queue is empty).
        """
        with self.lock:
            for i, task in enumerate(self.pending_tasks):

                # check for the task with 0 dependencies or all dependencies cleared
                is_ready = all(dep in self.completed_task_ids for dep in task.depends_on)

                if is_ready:
                    ready_task = self.pending_tasks.pop(i)
                    return ready_task

            # in case no task is found with 0 dependencies
            return None

    def mark_done(self, task_id: int) -> None:
        """Marks a task as completed, potentially unlocking dependent tasks."""
        with self.lock:
            self.completed_task_ids.add(task_id)

    def is_empty(self) -> bool:
        """Checks if there are any incomplete tasks left in the queue."""

        return len(self.pending_tasks) == 0
