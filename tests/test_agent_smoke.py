"""
Offline smoke test: mocks anthropic.Anthropic so we can validate the harness
logic (session state, day/question tracking, wrap-up + feedback contract)
without needing a real API key or network access.
"""
import json
import os
import sys
import types

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.agent import InterviewAgent, MIN_QUESTIONS, MIN_DAYS  # noqa: E402

# Scripted responses: alternate across curriculum days, then wrap up once
# both minimums are satisfied.
SCRIPT = [
    {"reply": "Hi! Let's start -- tell me how you designed your embedding pipeline.",
     "done": False, "meta": {"day": 7, "is_new_question": True}, "feedback": None},
    {"reply": "Got it. Follow-up: why that chunking strategy specifically?",
     "done": False, "meta": {"day": 7, "is_new_question": False}, "feedback": None},
    {"reply": "Makes sense. Next -- walk me through your retrieval routing logic.",
     "done": False, "meta": {"day": 10, "is_new_question": True}, "feedback": None},
    {"reply": "How did you design your multi-agent handoff?",
     "done": False, "meta": {"day": 22, "is_new_question": True}, "feedback": None},
    {"reply": "What would break if one agent timed out mid-handoff?",
     "done": False, "meta": {"day": 22, "is_new_question": False}, "feedback": None},
    {"reply": "Tell me about your MCP server -- what tools did it expose?",
     "done": False, "meta": {"day": 23, "is_new_question": True}, "feedback": None},
    # Model tries to wrap early at q=6/days=6 -- harness should reject this
    # and force a continuation (this response simulates that rejected attempt).
    {"reply": "Thanks, I think that covers it.",
     "done": True, "meta": {"day": None, "is_new_question": False},
     "feedback": {"summary": "premature", "strengths": [], "gaps": [], "next": []}},
    # Forced continuation responses (q goes 6 -> 7 -> 8):
    {"reply": "One more -- how did you containerize the deployment?",
     "done": False, "meta": {"day": 28, "is_new_question": True}, "feedback": None},
    {"reply": "And how are you monitoring it in production?",
     "done": False, "meta": {"day": 29, "is_new_question": True}, "feedback": None},
    {"reply": "One more -- how did you validate the structured outputs from your function-calling tools?",
     "done": False, "meta": {"day": 13, "is_new_question": True}, "feedback": None},
    {"reply": "Last one -- what would you change about the architecture with more time?",
     "done": False, "meta": {"day": 31, "is_new_question": True}, "feedback": None},
    {"reply": "Thanks, that's everything I need -- appreciate you walking me through it.",
     "done": True, "meta": {"day": None, "is_new_question": False},
     "feedback": {
         "summary": "Solid grasp of the RAG + agent pipeline with clear reasoning under follow-up.",
         "strengths": ["Clear explanation of retrieval routing", "Handled the MCP tool design well"],
         "gaps": ["Agent failure-handling reasoning was a bit shallow"],
         "next": ["Study timeout/retry patterns for multi-agent handoffs"],
     }},
]


class FakeBlock:
    def __init__(self, text):
        self.type = "text"
        self.text = text


class FakeResponse:
    def __init__(self, text):
        self.content = [FakeBlock(text)]


class FakeMessages:
    def __init__(self):
        self.i = 0

    def create(self, **kwargs):
        item = SCRIPT[self.i]
        self.i += 1
        return FakeResponse(json.dumps(item))


class FakeClient:
    def __init__(self):
        self.messages = FakeMessages()


def main():
    agent = InterviewAgent(api_key="fake")
    agent.client = FakeClient()

    candidate = json.load(open(os.path.join(os.path.dirname(__file__), "..", "data", "candidates.json")))["candidates"][2]  # Emily Chen

    session_id = "test-session-1"
    result = agent.start(session_id, candidate)
    print("START ->", result["reply"][:60], "| done:", result["done"])
    assert result["done"] is False

    turn_messages = [
        "I chunked by section with 200-token overlap, embedded with sentence-transformers.",
        "Overlap preserved context across boundaries so retrieval didn't cut off mid-answer.",
        "The router checks intent -- structured questions go to SQL, semantic ones to the vector DB, then I merge+dedupe.",
        "Each specialist agent owns one domain and a router agent delegates via LangGraph.",
        "It would fail the handoff and I'd need a retry/timeout wrapper -- honestly didn't fully handle that.",
        "It exposed search_claims and get_coverage as MCP tools over the SDK.",  # model then tries to wrap early -> harness rejects -> forces a continuation
        "Docker Compose for local, then a Helm chart for the k8s cluster with health checks.",
        "Prometheus for metrics and a Grafana dashboard for latency and tool-call failures.",
        "I validated everything through Pydantic models before executing the tool call.",
        "I'd add caching and better test coverage on the agent handoff paths.",
    ]

    state = agent.sessions[session_id]
    for msg in turn_messages:
        result = agent.turn(session_id, msg)
        print(f"[q={state.question_count}, days={sorted(state.days_covered)}] ->", result["reply"][:60], "| done:", result["done"])

    assert result["done"] is True, "interview should have concluded"
    assert "feedback" in result and result["feedback"] is not None
    assert state.question_count >= MIN_QUESTIONS, f"expected >= {MIN_QUESTIONS} questions, got {state.question_count}"
    assert len(state.days_covered) >= MIN_DAYS, f"expected >= {MIN_DAYS} days, got {state.days_covered}"

    print("\nFinal feedback object:")
    print(json.dumps(result["feedback"], indent=2))
    print("\nALL ASSERTIONS PASSED")


if __name__ == "__main__":
    main()
