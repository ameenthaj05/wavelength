# Wavelength

An AI-driven technical interview platform that conducts personalized, multi-turn interviews based on a candidate's AI Cohort learning journey.

Built for the ABTalks Hackathon — Technical Interview Evaluation Platform challenge.

*Tuned to what you actually built.*

---

## 🔗 Live Demo

**[wavelength.onrender.com](https://wavelength.onrender.com/)**

> **Note**: No login required — select the seeded demo candidate (**Sarah Jenkins**) from the Graduates Hub sidebar to start the evaluation.

---

## 🌟 What It Does

Rather than a scripted quiz, Wavelength conducts a realistic, adaptive technical interview grounded in a candidate's actual progress through a 31-day AI engineering curriculum — then produces structured, actionable feedback at the end.

- **Candidate Profiling**: Reads a candidate's completed missions, attempts, and skipped topics before the interview starts, and prioritizes weak/skipped areas first.
- **Minimums Enforcement**: Asks 8+ substantive questions across 4+ curriculum days.
- **Targeted Follow-ups**: Generates intelligent follow-up questions targeted at the specific kind of gap in an answer (vague, shallow, wrong, name-dropping) — not generic "can you elaborate?" prompts.
- **Rote Recitation Check**: Detects when an answer is recited from curriculum material versus genuinely explained in the candidate's own words.
- **Alignment Warnings**: Flags confidence/correctness mismatches (overconfidence, excessive hedging).
- **Diagnostic Feedback**: Produces a structured feedback report: readiness verdict, per-topic scores with evidence, communication score, and recommended review topics.

---

## 🏗️ Architecture

Wavelength runs as a 3-agent collaborative system rather than a single long prompt:

```
[Planner Agent] ──> [Interviewer Agent] ──> [Evaluator Agent]
```

- **Planner Agent** — runs once at session start. Calls MCP-pattern tool interfaces (`get_curriculum_day`, `get_candidate_signals`) to load the candidate's cohort history and build a prioritized, weighted topic path, weighted toward skipped/struggled topics.
- **Interviewer Agent** — manages the live turn loop. Retrieves target curriculum objectives via RAG (TF-IDF + cosine similarity), detects conceptual gaps in answers, generates targeted follow-ups, and adjusts difficulty as the interview progresses.
- **Evaluator Agent** — triggered at wrap-up. Synthesizes the full transcript, cross-checks confidence/correctness alignment, and produces the structured feedback payload.

Full design rationale, diagrams, and scoping trade-offs are in **[`SUBMISSION.md`](SUBMISSION.md)**. The AI-assisted development process and human-directed corrections are logged in **[`AI_TRANSCRIPT_LOG.md`](AI_TRANSCRIPT_LOG.md)**.

---

## 🌟 Key Differentiators

1. **Live Developer Reasoning Trace** — an expandable console showing the Planner and Interviewer's turn-by-turn internal reasoning (why a topic was prioritized, how an answer was scored, what follow-up strategy was chosen).
2. **Rote Recitation Detection** — flags candidates who copy curriculum phrasing verbatim instead of explaining concepts in their own words, via similarity scoring against ground-truth curriculum objectives.
3. **Interactive Waveform Report** — the entire interview visualized as a single scannable, color-coded trace (amplitude = answer depth, color = topic), with tap-to-replay on any segment.
4. **Standalone Shareable Report** — every completed interview gets a permanent `/report/{session_id}` link that renders independently of the live session.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | FastAPI (Python) |
| **Templates / Frontend** | Jinja2, vanilla JS, custom SVG (waveform component) |
| **LLM providers** | Google Gemini (`gemini-2.5-flash` direct HTTP via `httpx`) and Anthropic Claude (`claude-3-5-sonnet-20241022` official SDK) |
| **Retrieval** | In-memory TF-IDF + cosine similarity (`app/vector_store.py`) |
| **Persistence** | JSON-backed session store (`data/sessions.json`) |
| **Tool interfaces** | MCP-pattern tool calls (`get_curriculum_day`, `get_candidate_signals`) |

---

## 💻 Run Locally

### Requirements
- Python 3.10+
- A Google Gemini or Anthropic Claude API key.

```bash
# 1. Clone the repo
git clone https://github.com/ameenthaj05/wavelength.git
cd wavelength

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment variables
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY and/or ANTHROPIC_API_KEY

# 4. Run the server
uvicorn app.main:app --reload
```
Open **`http://localhost:8000`** in your browser.

---

## 🔑 Environment Variables

| Variable | Required | Description |
|---|---|---|
| **`GEMINI_API_KEY`** | One of these two | Google Gemini API key |
| **`ANTHROPIC_API_KEY`** | One of these two | Anthropic Claude API key |

> **LLM Provider Routing**: Only one key is strictly required — the LLM service detects which is present and routes calls accordingly. If both are set, the LLM service prioritizes Google Gemini (`gemini-2.5-flash`) by default.

---

## 📡 API Specification

Wavelength implements the endpoint contract defined in the hackathon's technical specification. See **[`SUBMISSION.md`](SUBMISSION.md)** for the full request/response schema and architecture diagram.

---

## 📂 Project Structure

```
wavelength/
├── app/
│   ├── main.py              # FastAPI app + routes
│   ├── agent.py             # Planner / Interviewer / Evaluator logic
│   ├── llm_service.py       # Dual-provider LLM abstraction
│   ├── vector_store.py      # TF-IDF / cosine retrieval
│   └── templates/
│       └── index.html       # Wavelength UI (Start / Interview / Wrap-Up / Report)
├── data/
│   ├── curriculum.json      # 31-day curriculum
│   └── candidates.json      # Candidate profiles (incl. seeded demo candidate)
├── tests/
│   └── test_agent_smoke.py  # Continuation harness + state validation smoke test
├── run_tests.py
├── requirements.txt
├── .env.example
├── SUBMISSION.md            # Full architecture walkthrough
├── AI_TRANSCRIPT_LOG.md     # AI-assisted development log
└── README.md
```

---

## 🧪 Testing

Run the test validation suites from the repository root:

```bash
# Run unit test discovery — validates LLM response formats
python run_tests.py

# Run smoke test — validates continuation harness & minimums enforcement
python tests/test_agent_smoke.py
```

*Verifies: interviews cannot end before 8 questions / 4 distinct curriculum days are covered; output metadata contains valid classifications for clarity, confidence, correctness, and hedging.*

---

## ⚠️ Known Limitations

- **Retrieval**: Uses local TF-IDF/cosine similarity rather than embedding-based search to avoid binary compilation issues (e.g. FAISS wheel builds) under the hackathon timebox. `vector_store.py` exposes an abstract interface for a drop-in swap to sentence-transformers + a vector database (e.g. Qdrant) in production.
- **MCP**: Tool-calling pattern is implemented directly in Python rather than via a standalone MCP server process to minimize setup overhead for reviewers running the project locally. The tool interface contract maps directly onto a network-connected MCP host.
- **Auth**: No authentication layer — out of scope per the hackathon problem statement.

---

## 🏆 Submission

Built for the ABTalks Hackathon. See **[`SUBMISSION.md`](SUBMISSION.md)** for the complete technical walkthrough and **[`AI_TRANSCRIPT_LOG.md`](AI_TRANSCRIPT_LOG.md)** for AI-assisted development transparency.
