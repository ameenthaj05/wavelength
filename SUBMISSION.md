# Technical Interview Evaluation Platform - Final Submission

This document serves as the final technical submission and architecture walkthrough for the live evaluation platform.

---

## Executive Summary

The platform is an intelligent technical assessment engine that conducts realistic, multi-turn conversational reviews of graduates from the AI Engineering cohort.

Rather than executing a basic sequential prompt script, the engine is structured as a **3-Agent Collaborative Architecture** (Planner $\rightarrow$ Interviewer $\rightarrow$ Evaluator) that integrates custom tooling layers, retrieval-grounded validation, and live waveform visualization:

*   **Planner Agent**: Runs at session start. It calls MCP tool interfaces to load candidate historical signals, identify weak/skipped topics, and build a prioritized, weighted technical path.
*   **Interviewer Agent**: Manages the conversational turn-loop. It retrieves target curriculum objectives, detects conceptual gaps (vague, wrong, shallow), generates follow-up probes, and dynamically updates difficulty.
*   **Evaluator Agent**: Triggered at wrap-up. It synthesizes full transcripts, cross-checks confidence/correctness alignment, and outputs structured performance diagnostics.

### 🌟 Key Differentiators
1.  **Live Developer Reasoning Trace**: An expandable developer drawer that displays the Planner and Interviewer's turn-by-turn internal reasoning (e.g. why a topic was prioritized, how correctness was scored, and what transition strategy was chosen).
2.  **Rote Recitation Similarity Detection**: Computes candidate text similarity scores against the curriculum objectives on the fly, flagging candidates who copy-paste textbook answers instead of explaining them in their own words.

---

## Minimum Requirements Checklist

The engine satisfies all core constraints specified in the Problem Statement:

| Requirement | Implementation Detail | Status |
| :--- | :--- | :---: |
| **8+ Substantive Questions** | Session minimum locked to 8 technical turns. | ✅ |
| **4+ Curriculum Days** | Ensures coverage across 4 distinct modules from the 31-day curriculum. | ✅ |
| **Maintain Context** | Full session state (plan, turn history, scores) persisted and passed across every turn; Evaluator reads the complete transcript, not a rolling window. | ✅ |
| **Reasoning-Driven Gaps** | Evaluates answers against specific categories (`shallow`, `wrong`, `vague`, `name_dropping`). | ✅ |
| **Structured JSON Feedback** | Compiles letters, scores, strengths, gaps, and recommended self-study modules. | ✅ |
| **FastAPI Specification** | Fully matches request/response schemas. | ✅ |

---

## Technical Design & Differentiators

```
                       [ Graduates Hub ]
                               │
                       (Sarah Jenkins Selected)
                               │
                       [ Planner Agent ]
                               │
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
   get_candidate_signals()               get_curriculum_day()
     (MCP Tool Call)                       (MCP Tool Call)
            │                                     │
            └──────────────────┬──────────────────┘
                               ▼
                    [ Structured Topic Plan ] ──────────> (Planner Trace Logged)
                               │
                               ▼
                     [ Interviewer Agent ]
                               │
                 ┌─────────────┴─────────────┐
                 ▼                           ▼
        VECTOR_STORE.search()       Auto-Difficulty Adjust
           (RAG Retrieval)           (Correctness Probing)
                 │                           │
                 ├───────────────────────────┴──────────> (Reasoning Trace Console)
                 ▼
          [ Live Turn Loop ] <── (Text, Multi-Turn)
                 │
                 ▼
         [ Evaluator Agent ] ───────────────────────────> (Recitation + Mismatch Flags)
                 │
                 ▼
    [ Standalone Parchment Report ]
```

### 1. Model Context Protocol (MCP) Integration
- **Scoping & Integration**: To minimize installation and setup runtime overhead for judges, running a separate background MCP server process was scoped out of the hackathon timebox. Instead, the MCP tool-calling pattern is implemented directly in Python. 
- The Planner Agent invokes these tools using standard JSON-RPC arguments, querying `get_curriculum_day(day)` and `get_candidate_signals(candidate)`. This provides a drop-in contract that can easily be mapped to a network-connected MCP host.

### 2. RAG In-Memory Retrieval
- **Retrieval Engine**: We implemented an in-memory TF-IDF and Cosine similarity vector search inside [`app/vector_store.py`](file:///c:/Users/Ameen%20Thaj/Downloads/interview-agent/interview-agent/app/vector_store.py).
- **Timebox Justification**: Standard TF-IDF + Cosine retrieval was chosen to guarantee fast query execution and remove binary compilation or package installation issues on Windows environments. The vector store defines an abstract interface, allowing a seamless swap to sentence-transformers and vector stores (e.g., Qdrant) in production.

### 3. Recitation & Mismatch Detectors
- **Recitation Flag**: Programmatically measures cosine similarity between candidate responses and target curriculum objectives. If similarity exceeds $0.45$, the candidate is flagged for verbatim copying (`recited` vs `explained`).
- **Confidence/Correctness Mismatch**: Detects overconfidence (low correctness, high confidence) and hedging (high correctness, low confidence) on every turn, rendering warnings on the report.

### 4. Interactive Waveform & Replay Mode
- **Signature UI**: Visualizes candidate performance as a live oscilloscope waveform.
- **Replay Inspector**: Tapping a waveform peak populates the question text, the student answer, and the developer trace details dynamically.

---

## Concrete Demo Metrics (Proof Point)

We seeded a candidate profile, **Sarah Jenkins (Seeded Demo)**, in [`data/candidates.json`](file:///c:/Users/Ameen%20Thaj/Downloads/interview-agent/interview-agent/data/candidates.json), with specific signals:
- **Attempts**: 4 attempts on Retrieval matching (Day 10 - high struggle).
- **Skips**: Skipped Day 22 (Agentic Orchestration) and Day 28 (Deployments).

**Demo Outcome**:
- On session start, the Planner Agent immediately parsed these signals and prioritized Days 22, 28, and 10 as the first three topics in the personalized plan, immediately surfacing skipped topics to probe gaps.

---

## Verification & Test Coverage

All tests run cleanly from the repository root:

```bash
# Run unit test discovery (validates LLM response formats)
python run_tests.py

# Run standalone smoke test (validates continuation harness)
python tests/test_agent_smoke.py
```

### Asserted Criteria
- **State Harness Integrity**: Verified that if the LLM attempts to wrap up before minimums are satisfied (8 questions, 4 distinct days), the harness rejects the done flag, nudges the LLM to continue, and successfully outputs evaluations once criteria are met.
- **Diagnostics Verification**: Asserted that output metadata contains valid classifications for clarity, confidence, correctness, and hedging.

---

## Known Limitations & Next Steps
- **Production MCP Server**: Transition the Python tool interfaces to a live MCP node hosting custom database connections.
- **Embeddings Upgrade**: Replace the TF-IDF vector retrieval with local sentence-transformers embeddings for deep semantic comparison.
- **Auth & Role Routing**: Add JWT security layers to separate candidates from grading administrators.
