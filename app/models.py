"""
Request/response models matching technical-spec.md exactly.
"""
from typing import Optional, List
from pydantic import BaseModel


class Candidate(BaseModel):
    # Kept loose (dict-like) on purpose -- the candidate.json schema has nested
    # "member", "missions", "signals" and we don't want to reject valid payloads
    # just because a field we don't use is missing/extra.
    class Config:
        extra = "allow"


class InterviewRequest(BaseModel):
    sessionId: str
    candidate: Optional[dict] = None   # present only on the first (start) call
    message: Optional[str] = None      # present on every subsequent turn
    mock: Optional[bool] = False       # starts the session in mock mode if True

    class Config:
        extra = "allow"


class Feedback(BaseModel):
    summary: str
    strengths: List[str]
    gaps: List[str]
    next: List[str]
    skills: Optional[dict] = None  # Maps cohort topics (RAG, Vector DBs, etc.) to 0-100 scores
    score: Optional[int] = None     # Overall score (0-100)
    grade: Optional[str] = None     # Letter grade (e.g. A, B+, C)
    status: Optional[str] = None    # Hire recommendation status (e.g. Strong Hire, Conditional Hire)
    
    # Rich structured breakdown indicators
    overall_readiness: Optional[str] = None
    topic_breakdown: Optional[List[dict]] = None
    communication_score: Optional[int] = None
    recommended_review: Optional[List[str]] = None
    strong_topics: Optional[List[str]] = None
    sample_ideal_answer: Optional[str] = None


class InterviewResponse(BaseModel):
    reply: str
    done: bool
    feedback: Optional[Feedback] = None
    clarity: Optional[int] = None
    confidence: Optional[int] = None

