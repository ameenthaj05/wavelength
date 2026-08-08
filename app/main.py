"""
AI Interview Agent -- HTTP layer.

Exposes endpoints for the interview session, candidates list, curriculum context,
and serves the single-page front-end application.
"""

import os
import json
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from dotenv import load_dotenv

from .agent import InterviewAgent
from .models import InterviewRequest

# Load environment variables from .env
load_dotenv()

app = FastAPI(title="AI Interview Agent")
agent = InterviewAgent()


@app.post("/api/interview")
async def interview(payload: InterviewRequest):
    if not payload.sessionId:
        raise HTTPException(status_code=400, detail="sessionId is required")

    try:
        if payload.candidate is not None:
            # Pass mock flag when starting a session
            result = agent.start(payload.sessionId, payload.candidate, mock=bool(payload.mock))
        elif payload.message is not None:
            result = agent.turn(payload.sessionId, payload.message)
        else:
            raise HTTPException(
                status_code=400,
                detail="Request must include either 'candidate' (to start) or 'message' (to continue).",
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Interview agent error: {e}")

    return JSONResponse(content=result)


@app.get("/api/candidates")
async def get_candidates():
    candidates_path = os.path.join(os.path.dirname(__file__), "..", "data", "candidates.json")
    if os.path.exists(candidates_path):
        try:
            with open(candidates_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error reading candidates: {e}")
    raise HTTPException(status_code=404, detail="candidates.json not found")


@app.get("/api/curriculum")
async def get_curriculum():
    curriculum_path = os.path.join(os.path.dirname(__file__), "..", "data", "curriculum.json")
    if os.path.exists(curriculum_path):
        try:
            with open(curriculum_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error reading curriculum: {e}")
    raise HTTPException(status_code=404, detail="curriculum.json not found")


@app.get("/api/session/{session_id}")
async def get_session_stats(session_id: str):
    state = agent.sessions.get(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "question_count": state.question_count,
        "days_covered": list(state.days_covered),
        "done": state.done,
        "candidate": state.candidate,
        "performance_log": state.performance_log,
        "feedback": state.feedback
      }


@app.get("/report/{session_id}", response_class=HTMLResponse)
async def serve_report(session_id: str):
    template_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    if os.path.exists(template_path):
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error serving template: {e}")
    raise HTTPException(status_code=404, detail="Template not found")


@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    template_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    if os.path.exists(template_path):
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error reading templates: {e}")
    return """
    <html>
        <head>
            <title>AI Interview Agent Setup</title>
            <style>
                body { font-family: sans-serif; padding: 2rem; background: #0f172a; color: #f8fafc; text-align: center; }
                .container { max-width: 600px; margin: 5rem auto; padding: 2rem; border-radius: 12px; background: #1e293b; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.5); }
                h1 { color: #38bdf8; }
                p { line-height: 1.6; color: #94a3b8; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>AI Interview Agent API</h1>
                <p>The backend server is running successfully!</p>
                <p>To view the visual dashboard interface, please ensure the frontend template is created at <code>app/templates/index.html</code>.</p>
            </div>
        </body>
    </html>
    """


@app.get("/health")
async def health():
    return {"status": "ok"}
