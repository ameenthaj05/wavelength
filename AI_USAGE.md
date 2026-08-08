# AI Usage Log - The Interview Agent

This log details the collaboration between the development team and the AI coding assistant (**Antigravity by Google DeepMind**) during the design, implementation, and verification of **The Interview Agent** for the ABTalks Hackathon.

---

## 1. AI Tools & Models Used
- **Primary AI Assistant**: Antigravity AI Coding Assistant (Google DeepMind)
- **Evaluation Brain Models**:
  - **Google Gemini**: `gemini-2.5-flash` (via direct HTTP integrations using `httpx`)
  - **Anthropic Claude**: `claude-3-5-sonnet-20241022` (via the official `anthropic` SDK)

---

## 2. Collaborative Timeline & Feature Implementation

### Phase 1: Architectural Design & Requirements Analysis
- **Goal**: Analyze curriculum, candidate JSON metrics, and API specifications.
- **AI Collaboration**: Brainstormed the abstraction pattern for supporting both Anthropic and Google Gemini based on environment variables, and mapped out the frontend timeline components.
- **Key Outcome**: Decided to build `app/llm_service.py` to wrap API calls independently of `agent.py`.

### Phase 2: Dual-Model LLM Abstraction
- **Goal**: Abstract model routing so the project runs on either Claude or Gemini dynamically.
- **AI Collaboration**: Drafted the `LLMService` wrapper class, standardizing chat transcript schemas (mapping standard user/assistant messages to Gemini user/model parts) and handling JSON responses.
- **Key Outcome**: Successful implementation of dynamic credentials detection.

### Phase 3: Conversation History Cleaning & Validation
- **Goal**: Keep internal prompts and premature wrap-up nudges out of the candidate's persistent chat log.
- **AI Collaboration**: Refactored `agent.py` to process system continuations using transient in-memory lists, saving only clean conversation turns to `data/sessions.json`. Added validation to check if the LLM-reported day number exists in the candidate's touched curriculum days.
- **Key Outcome**: Cleaner transcript prompts, robust state persistence, and verified smoke test passes.

### Phase 4: UI/UX Redesign & Advanced Mobile Drawer
- **Goal**: Match the exact visual layout, color palette (HSL), and typography of the ABTalks dashboard, ensuring mobile responsiveness.
- **AI Collaboration**: Overhauled `app/templates/index.html` with Plus Jakarta Sans & Inter font pairings, card light reflections, green socket animations, and a JavaScript-controlled sidebar overlay drawer for smaller viewports.
- **Key Outcome**: Premium visual dashboard with 100% responsive height viewport scaling.

---

## 3. Logged Prompts & Responses

### Prompt 1: Designing the LLM Abstraction
> **User Prompt**:
> *Create a utility `app/llm_service.py` that detects whether `GEMINI_API_KEY` or `ANTHROPIC_API_KEY` is present. If Gemini, it should construct direct HTTP requests to generative language endpoints to avoid installing new heavy SDK dependencies, standardizing the role mappings to user/model.*
> 
> **AI Contribution**:
> Wrote a unified class wrapper using `httpx` to handle standard REST payloads for Gemini, mapping roles from standard chat structures, while preserving the initialized `anthropic.Anthropic` client as a fallback.

### Prompt 2: Clean History Orchestration
> **User Prompt**:
> *Refactor the continuation loop in `agent.py` so that if the model tries to end early before minimums are met, the rejected wrap-up message and the system continue-nudge are sent in the subsequent API call but NEVER appended to the candidate's saved history.*
> 
> **AI Contribution**:
> Refactored the `_apply_turn` and `_force_continue` logic. Separated persistent history storage from temporary API payloads, ensuring that only the candidate's response and the interviewer's subsequent question are saved to the persistent session state.

### Prompt 3: Mobile Sidebar Drawer Layout
> **User Prompt**:
> *Update `index.html` with responsive styles. When the interview session is active, hide the timeline tracker in a drawer that slides in from the left when clicking a menu button. Ensure it fits portrait mobile screens.*
> 
> **AI Contribution**:
> Wrote responsive CSS using `body.session-active` class toggles. Hidden sidebar drawer slides out with transitions when clicked, overlays the chat, and closes upon clicking the chat frame.

---

## 4. Human-AI Contribution Ratios
- **System Architecture & Logic**: 30% Human Design, 70% AI Generation
- **Code Implementation**: 15% Human Refinements, 85% AI Coding
- **Testing & Quality Assurance**: 40% Human Validation, 60% AI Automations
