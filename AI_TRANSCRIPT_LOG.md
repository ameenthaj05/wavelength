# AI Prompts & Transcript Log — Wavelength

This log documents how AI coding assistance was used to build **Wavelength**, an AI-driven technical interview platform, for the ABTalks Hackathon. It's provided for transparency: what we directed, what the AI generated, and — most importantly — where we caught it getting things wrong and corrected it.

We used AI assistance heavily for implementation speed, but every architectural decision (the 3-agent Planner/Interviewer/Evaluator split, the MCP tool-calling pattern, the RAG scoping trade-off, the Wavelength design system and brand) originated from our own design process and was directed, reviewed, and in several cases corrected by us — not accepted as-is. The entries below include both.

---

## 1. AI Tools & Models Used

- **Coding assistant**: Antigravity (Google DeepMind), used for implementation, refactors, and boilerplate generation across the FastAPI backend and frontend.
- **Evaluation/interview models**:
  - Google Gemini `gemini-2.5-flash` — direct HTTP integration via `httpx` (avoids a heavy SDK dependency).
  - Anthropic Claude `claude-3-5-sonnet-20241022` — via the official `anthropic` SDK.
- Model routing is abstracted behind `app/llm_service.py` so the interview engine runs on either provider depending on which API key is present in the environment — this was a deliberate architecture decision, not something the AI suggested unprompted; we wanted judges to be able to run the project regardless of which key they had available.

---

## 2. Collaborative Timeline

### Phase 1 — Architecture & Requirements Analysis
**Our decision:** Structure the engine as three distinct agents (Planner → Interviewer → Evaluator) rather than one long prompt, so personalization, questioning, and scoring stay separable and testable.
**AI's role:** Helped draft the initial module boundaries and the `LLMService` abstraction pattern once the architecture was specified.
**Outcome:** `app/llm_service.py` decouples model calls from `agent.py`, so the 3-agent structure isn't tied to a single provider.

### Phase 2 — Dual-Model LLM Abstraction
**Prompt:** *"Detect whether `GEMINI_API_KEY` or `ANTHROPIC_API_KEY` is present. If Gemini, use direct HTTP requests to the generative language endpoint rather than a new SDK dependency. Standardize role mapping to user/model."*
**AI's contribution:** Wrote the `httpx`-based wrapper and role-mapping logic.
**Where we corrected it:** The first version silently defaulted to Gemini's chat format even when only the Anthropic key was present, causing malformed payloads on Claude runs. We had it add explicit key-detection branching with a hard failure (not a silent fallback) if neither key is set — this was a real bug the AI introduced that we caught in testing, not something we asked for up front.

### Phase 3 — Conversation History Cleaning & State Validation
**Prompt:** *"If the model tries to end the interview before minimums are met, the rejection message and continue-nudge should be sent in the next API call but never saved to the candidate's persistent history."*
**AI's contribution:** Refactored `_apply_turn` and `_force_continue` to separate transient API payloads from persisted session state.
**Where we corrected it:** The initial refactor saved the *nudge* to history but not the model's follow-up response to it, breaking transcript continuity on replay. We caught this via the smoke test (`test_agent_smoke.py`) failing on a continuation-count assertion, traced it to the save order, and had it fixed to persist only clean, complete turns.
**Our decision, not AI's:** Adding curriculum-day validation (checking the LLM-reported day against the candidate's actual touched days) — this was a deliberate hallucination guard we specified after noticing the model occasionally referenced days outside the candidate's curriculum.

### Phase 4 — Wavelength Design System Implementation
**Our decision:** Design and specify the full Wavelength visual identity ourselves — the ink/parchment/signal/calibrate/friction/slate palette, the Fraunces + JetBrains Mono + Inter type system, and the signature waveform component that runs across the Start, Live Interview, Wrap-Up, and Report screens.
**Prompt:** *"Implement `app/templates/index.html` to this design system: Fraunces for narrative/report copy, JetBrains Mono for technical/transcript text, the specified color tokens, and a custom SVG waveform component (not a chart library) driven by the per-question score array. Add a responsive sidebar drawer for the topic radar panel on mobile."*
**AI's contribution:** Implemented the CSS token system, the SVG waveform path generation from the score array, and the `body.session-active` class-based drawer toggle with slide/overlay transitions.
**Where we corrected it:** The first waveform implementation re-rendered the entire SVG path on every score update, causing a visible flash instead of a smooth draw. We asked it to animate only the newly appended path segment instead of redrawing the full path — this fixed the "grows as you go" behavior the design called for.
**Outcome:** A cohesive, responsive UI matching the design spec across all four screens, with the waveform as a shared component reused (idle/live/annotated variants) rather than rebuilt per page.

---

## 3. Where We Overrode the AI

Being transparent about disagreements is part of showing real engineering judgment, not just prompt-and-accept:

- **RAG retrieval method:** The AI's first suggestion was to pull in `sentence-transformers` for embedding-based retrieval. We overrode this in favor of TF-IDF + cosine similarity in `app/vector_store.py`, specifically to avoid binary compilation issues on Windows dev machines under the hackathon timebox — a deliberate trade-off, documented in our submission's Known Limitations, not an oversight.
- **MCP integration:** The AI initially proposed standing up a full local MCP server process. We scoped this down to a direct Python tool-calling pattern (`get_curriculum_day`, `get_candidate_signals`) with the same call contract, to reduce setup friction for judges running the project locally.
- **Visual design direction:** An early pass matched a generic dashboard template. We rejected it and specified the Wavelength system (custom palette, type pairing, and the waveform-as-signature-element concept) explicitly, because a templated look wouldn't differentiate the submission.

---

## 4. Human-AI Contribution Summary

Rather than a flat percentage split, here's a breakdown by *kind of contribution*, since that's a more honest signal than a single ratio:

| Area | Human-directed | AI-generated |
|---|---|---|
| Agent architecture (Planner/Interviewer/Evaluator split, MCP/RAG scoping decisions) | Fully specified by us | AI implemented against our spec |
| Design system (palette, type, waveform concept, screen flow) | Fully specified by us | AI implemented against our spec |
| Boilerplate & wiring (FastAPI routes, CSS, HTTP client code) | Reviewed and corrected | Majority AI-written |
| Bug fixes during implementation | Diagnosed and directed by us (see Section 3) | AI implemented the fix once diagnosed |
| Testing & verification criteria | Defined by us (what "passing" means) | AI wrote test scaffolding against our criteria |

We used AI assistance to move fast on implementation, while architecture, design, and debugging direction stayed a human-driven process — the corrections logged above are the clearest evidence of that.
