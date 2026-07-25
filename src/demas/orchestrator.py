"""
The main engine coordinating the DeMAS framework components.
"""
import threading
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import PromptTemplate
from .models import Task
from .task_queue import TaskQueue
from .shared_context import VerifiedSharedContext
from .worker_node import WorkerNode
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import PromptTemplate
from typing import Any

class GeneratedTask(BaseModel):
    name: str = Field(description="Description of the new task.")

class OrchestratorPlan(BaseModel):
    is_goal_met: bool = Field(description="True if the main goal is achieved based on current context.")

    new_tasks: List[GeneratedTask] = Field(default_factory=list, description="New tasks to be added if goal is not met.")

    final_answer: Optional[str] = Field(default=None, description="The final synthesized answer if the goal is met.")

class DemasOrchestrator:

    """
    Provides a high-level API to initialize the DeMAS system, dynamically break down
    the main goal, manage the task generation loop, and coordinate workers.
    """

    def __init__(self, llm: Any, num_workers: int = 3):
        """
        Initializes the orchestrator, queue, context, and worker pool.
        """
        self.llm = llm
        self.num_workers = num_workers

        self.queue = TaskQueue()
        self.context = VerifiedSharedContext(verifier_llm=llm)
        self.structured_planner = self.llm.with_structured_output(OrchestratorPlan)

        # every new task gets a unique id
        self.next_task_id = 1

        self.planner_prompt = PromptTemplate.from_template(
            "Main Goal: {goal}\n\n"
            "Current Verified Knowledge gathered by agents:\n{shared_knowledge}\n\n"
            "Analyze if the Main Goal has been completely answered. "
            "If yes, set is_goal_met to true and provide the final_answer. "
            "If no, generate the next logical sub-tasks to achieve the goal."
        )

    def start_workers_and_wait(self):
        """Starts the worker threads and waits for them to empty the queue."""
        threads = []

        for i in range(self.num_workers):
            # create a new worker
            worker = WorkerNode(llm=self.llm, context=self.context, agent_id=f"Worker{i + 1}")

            t = threading.Thread(target=worker.start_working_on, args=(self.queue,))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

    def evaluate_and_generate(self, main_goal: str) -> Optional[str]:
        """
        Uses LLM to check if the goal is met. If not, generates new tasks and adds them to the queue.
        Returns final_answer if the goal is met, otherwise None.
        """

        snapshot = self.context.get_snapshot()

        if snapshot:
            knowledge_str = "\n".join([f"- {item.claim}" for item in snapshot])
        else:
            knowledge_str = "No knowledge gathered yet."

        print("\n Orchestrator evaluating progress...")
        prompt_val = self.planner_prompt.invoke({
            "goal": main_goal,
            "shared_knowledge": knowledge_str
        })

        plan: OrchestratorPlan = self.structured_planner.invoke(prompt_val)

        if plan.is_goal_met:
            return plan.final_answer
        print(f"--- Goal not met yet. Generating {len(plan.new_tasks)} new tasks...")

        for g_task in plan.new_tasks:
            print(f"    -> [Task {self.next_task_id}]: {g_task.name}")
            new_task = Task(
                id=self.next_task_id,
                name=g_task.name,
                depends_on=[]
            )
            self.queue.add_task(new_task)
            self.next_task_id += 1

        return None

    def run(self, main_goal: str) -> str:
        """
        The main entry point for the user.
        Loop continues until evaluate_and_generate says the goal is met.
        """
        print(f"Starting DeMAS Engine for Goal: {main_goal}")

        while True:
            if self.queue.is_empty():
                # 1. Orchestrator -> (Evaluate & Generate)
                final_answer = self.evaluate_and_generate(main_goal)

                # 2. if we found the answer, exit the loop
                if final_answer:
                    print("\n Goal Achieved!")
                    return final_answer

                # 3. if new tasks are added, then wake the workers and start the work again
                self.start_workers_and_wait()


