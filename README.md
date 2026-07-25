[![PyPI version](https://img.shields.io/pypi/v/decmas.svg)](https://pypi.org/project/decmas/)    # <--users can test this framework 
# DeMAS: Decentralized Multi-Agent System

![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Framework](https://img.shields.io/badge/Framework-Langchain-green)

DeMAS is a lightweight, high-performance Python framework inspired by Stanford's research on **Decentralized Language Models (DeLM)**. It moves away from traditional "Router-Agent" bottlenecks by implementing a decentralized architecture where multiple autonomous agents operate in parallel, sharing a globally verified memory context.

## The Architecture Paradigm

*Reference Architecture from Stanford's DeLM Paper:*
![DeMAS Architecture Reference](assets/architecture.png)

### Centralized vs Decentralized
Traditional Multi-Agent Systems rely on a single Main Agent (Router) that becomes a bottleneck as it orchestrates every sub-agent. DeMAS distributes the workload across parallel agents that communicate asynchronously through a Shared Context and a Task Queue.

```mermaid
graph LR
    subgraph Centralized [Centralized Architecture - Bottlenecked]
        direction TB
        Router((Router Agent)) -->|Assigns Tasks| A1[Agent 1]
        Router -->|Assigns Tasks| A2[Agent 2]
        Router -->|Assigns Tasks| A3[Agent 3]
        A1 -->|Waits for| Router
        A2 -->|Waits for| Router
        A3 -->|Waits for| Router
    end

    subgraph Decentralized [DeMAS Architecture - Scalable]
        direction TB
        Q[(Task Queue)]
        C[(Shared Context)]
        W1[Worker 1]
        W2[Worker 2]
        W3[Worker 3]
        
        Q -.->|Claims Task| W1
        Q -.->|Claims Task| W2
        Q -.->|Claims Task| W3
        
        W1 -.->|Proposes Updates| C
        W2 -.->|Proposes Updates| C
        W3 -.->|Proposes Updates| C
    end
    
    style Centralized fill:#f9f9f9,stroke:#e0e0e0,stroke-width:2px
    style Decentralized fill:#f0f8ff,stroke:#b0c4de,stroke-width:2px
    style Router fill:#ffcccb,stroke:#ff0000,stroke-width:2px
    style Q fill:#e6e6fa,stroke:#9370db,stroke-width:2px
    style C fill:#d8bfd8,stroke:#8a2be2,stroke-width:2px
    style W1 fill:#e8f5e9,stroke:#388e3c
    style W2 fill:#e8f5e9,stroke:#388e3c
    style W3 fill:#e8f5e9,stroke:#388e3c
```

### The DeMAS Core Loop

DeMAS relies on three core components operating in perfect harmony. The execution loop guarantees verifiable knowledge progression without race conditions.

```mermaid
graph TD
    classDef memory fill:#e1f5fe,stroke:#0288d1,stroke-width:2px;
    classDef worker fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px;
    classDef queue fill:#fff3e0,stroke:#f57c00,stroke-width:2px;
    classDef orchestrator fill:#e8f5e9,stroke:#388e3c,stroke-width:2px;

    O[Orchestrator Planner]:::orchestrator
    Q[(Async Task Queue)]:::queue
    C[(Verified Shared Context)]:::memory
    
    subgraph Parallel Node Execution
        direction LR
        W1[Worker Node A]:::worker
        W2[Worker Node B]:::worker
        W3[Worker Node C]:::worker
    end

    O -->|1. Dynamically generates task graph| Q
    Q -->|2. Concurrently fetches ready tasks| W1
    Q -->|2. Concurrently fetches ready tasks| W2
    Q -->|2. Concurrently fetches ready tasks| W3
    
    W1 -->|3. Proposes claims| C
    W2 -->|3. Proposes claims| C
    W3 -->|3. Proposes claims| C
    
    C -->|4. LLM Verifier filters hallucinations| C
    C -.->|5. Reads global state to check if goal is met| O
```

## Key Features

- **Decentralized Parallel Execution:** No central bottleneck. Multiple worker nodes run concurrently using standard Python threading.
- **Verified Shared Context:** Agents do not communicate directly. They propose updates to a shared memory. Updates are strictly verified by an LLM before admission, entirely eliminating downstream hallucination chains.
- **Asynchronous Task Queue:** Dynamic generation of sub-tasks by the orchestrator. Workers automatically claim ready tasks as soon as their local dependencies are resolved.
- **Native Langchain Integration:** Built entirely on `langchain-core`, allowing you to plug in OpenAI, Anthropic, Groq, or local models effortlessly.

## Installation

Install directly from PyPI:

```bash
pip install decmas
```

*(For developers: If you want to modify the framework, you can clone the repository and run `pip install -e .`)*

*Note: You must also install your preferred LLM provider, e.g., `pip install langchain-openai` or `pip install langchain-groq`.*

## Quick Start

Here is a minimal example of how to initialize the engine and run a complex goal:

```python
import os
from langchain_groq import ChatGroq
from demas import DemasOrchestrator

# Initialize your LLM
os.environ["GROQ_API_KEY"] = "your-api-key"
llm = ChatGroq(model="llama3-70b-8192", temperature=0)

# Initialize the Engine with 3 parallel workers
engine = DemasOrchestrator(llm=llm, num_workers=3)

# Pass a complex goal to the orchestrator
goal = "Research LangGraph, extract its top 3 features, and compare it with Autogen."

# Run the Framework
final_answer = engine.run(goal)
print("FINAL RESULT:", final_answer)
```

---
*Architected for next-generation Agentic AI capabilities.*
