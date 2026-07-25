"""
Represents an individual agent executing tasks in parallel.
"""
import time
from typing import Any
from .task_queue import TaskQueue
from .shared_context import VerifiedSharedContext
from .models import Task
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field

class AgentOutput(BaseModel):
    claim: str = Field(...,description="A short, concise summary of the findings or answer for this task.")
    evidence: str = Field(...,description="The detailed explanation, logic, or raw data that supports the claim.")

class WorkerNode:
    """
    An autonomous worker that claims tasks, reads the shared context,
    performs local reasoning using an LLM, and writes back verified updates.
    """
    def __init__(self, llm: BaseChatModel, context: VerifiedSharedContext, agent_id: str = "Worker-1"):
        """
        Initializes the worker with its reasoning LLM and access to the shared notebook.
        """
        self.agent_id = agent_id
        self.context = context

        self.structured_llm = llm.with_structured_output(AgentOutput)

        self.agent_prompt = PromptTemplate.from_template(
            "You are an intelligent research agent. Your task is to solve the current problem.\n\n"
            "Here is the knowledge we have gathered so far (from other agents):\n"
            "{shared_knowledge}\n\n"
            "Your specific task to execute right now:\n"
            "{task_name}\n\n"
            "Do your research/reasoning and provide a claim and evidence."
        )



    def execute_task(self, task: Task) -> bool:
        """
        The core execution loop for a single task:
        1. Read the context snapshot.
        2. Perform reasoning (using LLM).
        3. Propose updates to the context.
        """

        # 1. Read progress made so far from the shared memory
        snapshot = self.context.get_snapshot()

        if snapshot:
            knowledge_str = "\n".join(f"- {item.claim}" for item in snapshot)
        else:
            knowledge_str = "No prior knowledge yet."

        prompt_val = self.agent_prompt.invoke({
            "shared_knowledge": knowledge_str,
            "task_name": task.name
        })

        result: AgentOutput = self.structured_llm.invoke(prompt_val)

        task.result = result.claim

        # 3. send the result for verification in the shared memory
        print(f"[{self.agent_id}] Proposing update for task {task.id}...")
        is_admitted = self.context.propose_update(
                claim=result.claim,
                raw_evidence=result.evidence,
                task_id=task.id
        )

        return is_admitted

    def start_working_on(self, queue: TaskQueue) -> None:
        """
        Continuously polls the queue for ready tasks and executes them until
        the queue is exhausted.
        """
        while not queue.is_empty():
            task = queue.get_ready_task()

            if task is None:  # means there are tasks that have some dependencies not completed yet, wait for them a while.

                time.sleep(1)
                continue

            success = self.execute_task(task)

            if success:
                queue.mark_done(task.id)
                print(f"[{self.agent_id}] Task {task.id} marked as DONE.\n")
            else:
                print(f"[{self.agent_id}] Verification failed for Task {task.id}. Will retry.\n")
                queue.add_task(task)  # append this is the queue again for retry

        print(f"[{self.agent_id}] No more tasks. Going to sleep zZz...")

