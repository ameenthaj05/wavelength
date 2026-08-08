# Wavelength

An AI-driven technical interview platform that conducts personalized, multi-turn technical reviews of AI Cohort graduates based on their learning journey.

---

## 🚀 Live Demo

**[Wavelength Live Platform](https://wavelength.onrender.com)** *(Example Render instance URL. Please warm up the service if loading is slow on first click).*

---

## 🏗️ Architecture

Wavelength uses a **3-Agent Collaborative Architecture** to make the evaluation lifecycle reasoning-driven rather than scripted:
1. **Planner Agent**: Reads historical graduate performance signals via local tool contracts and designs a prioritized path.
2. **Interviewer Agent**: Manages the conversational question/answer turn loops, retrieving curriculum days and digging into detected gaps.
3. **Evaluator Agent**: Audits the completed transcripts, flags rote recitations, and synthesizes performance report metrics.

For details, check out:
- **[`SUBMISSION.md`](file:///c:/Users/Ameen%20Thaj/Downloads/interview-agent/interview-agent/SUBMISSION.md)**: Full architecture flow diagrams, minimums checklist, and local verification trails.
- **[`PROMPTS.md`](file:///c:/Users/Ameen%20Thaj/Downloads/interview-agent/interview-agent/PROMPTS.md)**: Prompts timeline, model settings, and engineering corrections logs.

---

## 💻 Run Locally

### 1. Installation
Clone the repository and install dependencies:
```bash
git clone https://github.com/your-username/wavelength.git
cd wavelength
pip install -r requirements.txt
```

### 2. Configure Environment Secrets
Copy the environment template and insert your API credentials:
```bash
cp .env.example .env
# Open .env and add your GEMINI_API_KEY or ANTHROPIC_API_KEY
```

### 3. Launch Server
Start the Uvicorn ASGI server:
```bash
uvicorn app.main:app --reload --port 8000
```
Open **`http://localhost:8000`** in your browser.

---

## 🛠️ Tech Stack

- **Backend**: FastAPI, Python (Uvicorn ASGI)
- **AI Brains**: Google Gemini (`gemini-2.5-flash` direct HTTP integration) / Anthropic Claude (`claude-3-5-sonnet-20241022`)
- **Data Engine**: Local in-memory TF-IDF + Cosine string similarity index (for zero-dependency Windows host setup)
- **Frontend**: Vanilla HTML / JS with custom CSS HSL theme tokens (midnight ink / warm parchment / signal amber)

---

## 🧪 Demo Credentials

Select **Sarah Jenkins (Seeded Demo)** from the Graduates Hub sidebar on the landing view (no passwords required). The Planner Agent will extract her skips and struggles to customize the questioning path automatically.
