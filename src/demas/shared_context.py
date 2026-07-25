"""
Manages the verified shared memory (the global problem state).
"""
from typing import List, Any
from .models import ContextUpdate
import threading
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field

class VerificationResult(BaseModel):
    is_approved : bool = Field(..., description="True if the claim is completely supported by the evidence, False otherwise.")
    reason: str = Field(description="Brief reason for approval or rejection.")

class VerifiedSharedContext:
    """
    The core communication substrate for DeMAS.
    Stores compact, reusable problem state. Every update must pass admission-time verification.
    """
    def __init__(self, verifier_llm: BaseChatModel):
        """
        Initializes the context with an LLM instance used for verifying claims.
        """
        self.memory : List[ContextUpdate] = []

        self.structured_verifier  = verifier_llm.with_structured_output(VerificationResult)

        self.lock = threading.Lock()

        # prompt for the verifier LLM

        self.verification_prompt = PromptTemplate.from_template(
            "You are a strict verifier. Your job is to check if the CLAIM is completely supported by the EVIDENCE.\n"
            "CLAIM: {claim}\n"
            "EVIDENCE: {evidence}\n"
        )

    def get_snapshot(self) -> List[ContextUpdate]:
        """
        Returns a lock-free snapshot of the current verified memory.
        Agents read this at dispatch time.
        """

        # returning a copy of memory so the agent does not accidentally change the original memory
        with self.lock:
            return list(self.memory)


    def propose_update(self, claim: str, raw_evidence: str, task_id: int) -> bool:
        """
        Submits an update for verification. 
        If the verifier_llm confirms the claim is supported by the raw_evidence, 
        it is admitted to the shared memory.
        
        Returns: True if admitted, False if rejected.
        """

        formatted_prompt = self.verification_prompt.invoke({
                "claim" : claim,
                "evidence" : raw_evidence
             })

        response: VerificationResult = self.structured_verifier.invoke(formatted_prompt)

        if response.is_approved:
            update = ContextUpdate(
                claim=claim,
                evidence=raw_evidence,
                source_task_id=task_id
            )

            with self.lock:
                self.memory.append(update)
                return True

        print(f"Rejection because : {response.reason}")
        return False


