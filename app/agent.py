"""
InterviewAgent
==============

Claude or Gemini is the "interviewer brain": it decides what to ask, how to follow up,
and when to wrap up. This module is the harness around it -- it owns session
state, builds the system prompt from the candidate + curriculum data, enforces
the contract from technical-spec.md (>=8 questions across >=4 distinct
curriculum days, structured feedback on completion), and guarantees the HTTP
layer always gets valid JSON back even if the model wobbles.
"""

import json
import os
import re
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Set

import anthropic
from .llm_service import LLMService
from .vector_store import SimpleVectorStore

MODEL = "claude-3-5-sonnet-20241022"
MIN_QUESTIONS = 8
MIN_DAYS = 4
MAX_QUESTIONS = 14  # safety valve so a confused model can't loop forever

CURRICULUM_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "curriculum.json")
SESSIONS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "sessions.json")


def _load_curriculum() -> dict:
    with open(CURRICULUM_PATH) as f:
        return json.load(f)


CURRICULUM = _load_curriculum()
DAYS_BY_NUMBER = {d["day"]: d for d in CURRICULUM["days"]}
VECTOR_STORE = SimpleVectorStore(CURRICULUM["days"])


def get_curriculum_day(day: int) -> dict:
    """Exposed as local MCP tool for retrieving curriculum details."""
    return DAYS_BY_NUMBER.get(day, {})


def get_candidate_signals(candidate: dict) -> dict:
    """Exposed as local MCP tool for extracting candidate performance signals."""
    return candidate.get("signals", {})


@dataclass
class SessionState:
    candidate: dict
    history: list = field(default_factory=list)     # [{"role": "user"/"assistant", "content": str}]
    question_count: int = 0
    days_covered: set = field(default_factory=set)
    done: bool = False
    mock: bool = False
    mock_index: int = 0
    
    # Structured InterviewState fields
    interview_plan: list = field(default_factory=list)      # List of day numbers
    current_topic_idx: int = 0
    follow_ups_count: int = 0
    hedging_count: int = 0
    performance_log: list = field(default_factory=list)     # List of dict evaluations
    feedback: Optional[dict] = None
    
    # Advanced state indicators
    inject_curveball: bool = False
    last_turn_similarity: float = 0.0
    last_turn_objective: str = ""


class InterviewAgent:
    def __init__(self, api_key: Optional[str] = None):
        self.llm_service = LLMService(api_key=api_key)
        # Keep self.client for backwards compatibility & smoke test mocking
        self.client = self.llm_service.anthropic_client
        self.sessions: dict[str, SessionState] = {}
        self._load_sessions()

    # ------------------------------------------------------------------ #
    # Session Persistence
    # ------------------------------------------------------------------ #

    def _load_sessions(self):
        if os.path.exists(SESSIONS_PATH):
            try:
                with open(SESSIONS_PATH, "r") as f:
                    data = json.load(f)
                    for sid, sdata in data.items():
                        self.sessions[sid] = SessionState(
                            candidate=sdata["candidate"],
                            history=sdata["history"],
                            question_count=sdata["question_count"],
                            days_covered=set(sdata["days_covered"]),
                            done=sdata["done"],
                            mock=sdata.get("mock", False),
                            mock_index=sdata.get("mock_index", 0),
                            interview_plan=sdata.get("interview_plan", []),
                            current_topic_idx=sdata.get("current_topic_idx", 0),
                            follow_ups_count=sdata.get("follow_ups_count", 0),
                            hedging_count=sdata.get("hedging_count", 0),
                            performance_log=sdata.get("performance_log", []),
                            feedback=sdata.get("feedback", None),
                            inject_curveball=sdata.get("inject_curveball", False),
                            last_turn_similarity=sdata.get("last_turn_similarity", 0.0),
                            last_turn_objective=sdata.get("last_turn_objective", "")
                        )
            except Exception:
                self.sessions = {}
        else:
            self.sessions = {}

    def _save_sessions(self):
        try:
            data = {}
            for sid, state in self.sessions.items():
                data[sid] = {
                    "candidate": state.candidate,
                    "history": state.history,
                    "question_count": state.question_count,
                    "days_covered": list(state.days_covered),
                    "done": state.done,
                    "mock": getattr(state, "mock", False),
                    "mock_index": getattr(state, "mock_index", 0),
                    "interview_plan": getattr(state, "interview_plan", []),
                    "current_topic_idx": getattr(state, "current_topic_idx", 0),
                    "follow_ups_count": getattr(state, "follow_ups_count", 0),
                    "hedging_count": getattr(state, "hedging_count", 0),
                    "performance_log": getattr(state, "performance_log", []),
                    "feedback": getattr(state, "feedback", None),
                    "inject_curveball": getattr(state, "inject_curveball", False),
                    "last_turn_similarity": getattr(state, "last_turn_similarity", 0.0),
                    "last_turn_objective": getattr(state, "last_turn_objective", "")
                }
            os.makedirs(os.path.dirname(SESSIONS_PATH), exist_ok=True)
            with open(SESSIONS_PATH, "w") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    # Public entry points
    # ------------------------------------------------------------------ #

    def start(self, session_id: str, candidate: dict, mock: bool = False) -> dict:
        state = SessionState(candidate=candidate, mock=mock, mock_index=0)
        
        # --- MCP-TOOL PERSONALIZATION ENGINE ---
        # Analyze candidate's history using local MCP tools
        signals = get_candidate_signals(candidate)
        missions = candidate.get("missions", [])
        
        weak_signals = []
        mastered_topics = []
        neutral_topics = []
        
        for m in missions:
            day = m.get("day")
            if day is None:
                continue
            day_data = get_curriculum_day(day)
            attempts = m.get("attempts", 1)
            passed = m.get("passed", False)
            skipped = m.get("skipped", False)
            
            # Skips, multiple failures or high attempts counts represent weak signals
            if skipped or not passed or attempts >= 3:
                weak_signals.append(day)
            elif attempts == 1 and passed:
                mastered_topics.append(day)
            else:
                neutral_topics.append(day)
                
        # Sort plan: weak signals first, then neutral, and mastered at the end
        interview_plan = weak_signals + neutral_topics + mastered_topics
        if not interview_plan:
            interview_plan = sorted(list(DAYS_BY_NUMBER.keys()))
            
        state.interview_plan = interview_plan
        state.current_topic_idx = 0
        state.follow_ups_count = 0
        state.hedging_count = 0
        state.feedback = None
        state.performance_log = []
        
        # Log the initial planner reasoning trace
        plan_trace = (
            f"Planner Agent Action: Initialized session. Prioritizing candidate weak signals first. "
            f"Weak signals detected (skipped/failed/attempts >= 3): {weak_signals}. "
            f"Neutral signals: {neutral_topics}. Mastered signals: {mastered_topics}. "
            f"Plan built: [{', '.join(f'Day {d}' for d in interview_plan)}]."
        )
        
        state.performance_log.append({
            "turn": 0,
            "day": None,
            "clarity": 5,
            "confidence": 5,
            "correctness": 5,
            "gap_type": "none",
            "hedging_detected": False,
            "recitation_flag": "explained",
            "recitation_reason": "Session initialization.",
            "similarity_score": 0.0,
            "mismatch_flag": "aligned",
            "reasoning_trace": plan_trace,
            "question": "System Initialization",
            "answer": "Profile loaded and evaluated."
        })
        
        self.sessions[session_id] = state
        self._save_sessions()
        
        reply, meta, feedback = self._call_model(
            state,
            user_message=None,
            kickoff=True,
        )
        return self._apply_turn(state, reply, meta, feedback, user_message=None, kickoff=True)

    def turn(self, session_id: str, message: str) -> dict:
        state = self.sessions.get(session_id)
        if state is None:
            # Defensive placeholder setup
            state = SessionState(candidate={"member": {"name": "Candidate"}, "missions": []})
            self.sessions[session_id] = state
            self._save_sessions()

        if state.done:
            return {
                "reply": "This interview has already concluded. Thanks again for your time.",
                "done": True,
            }

        reply, meta, feedback = self._call_model(state, user_message=message, kickoff=False)
        return self._apply_turn(state, reply, meta, feedback, user_message=message, kickoff=False)

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #

    def _apply_turn(self, state: SessionState, reply: str, meta: dict, feedback: Optional[dict], user_message: Optional[str], kickoff: bool) -> dict:
        wants_to_wrap = feedback is not None
        minimums_met = state.question_count >= MIN_QUESTIONS and len(state.days_covered) >= MIN_DAYS
        force_wrap = state.question_count >= MAX_QUESTIONS

        if getattr(state, "mock", False):
            from .mock_script import SCRIPT
            # If we reached the final item of the script, mark minimums as met
            if getattr(state, "mock_index", 0) >= len(SCRIPT):
                minimums_met = True

        if wants_to_wrap and not minimums_met and not force_wrap:
            # Reject early wrap-up and force the model to ask a continuation question
            reply, meta, feedback = self._force_continue(state, user_message, kickoff, premature_reply=reply)
            # Re-evaluate wrap flags
            wants_to_wrap = feedback is not None
            minimums_met = state.question_count >= MIN_QUESTIONS and len(state.days_covered) >= MIN_DAYS
            if getattr(state, "mock", False):
                from .mock_script import SCRIPT
                if getattr(state, "mock_index", 0) >= len(SCRIPT):
                    minimums_met = True

        # Update tracked stats from the finalized metadata of this turn
        day = meta.get("day") if meta else None
        is_new_question = bool(meta.get("is_new_question", True)) if meta else True
        
        # Verify day was actually touched by candidate to avoid hallucination counts
        relevant_days = {m.get("day") for m in state.candidate.get("missions", []) if m.get("day") is not None}
        if day is not None:
            try:
                day_int = int(day)
                if getattr(state, "mock", False) or day_int in relevant_days:
                    state.days_covered.add(day_int)
            except (ValueError, TypeError):
                pass

        # Extract previous question asked
        prev_question = "Welcome! Before we dive into the details, give me a quick 30-second overview of the Capstone project you built for this cohort."
        assistant_msgs = [h for h in state.history if h.get("role") == "assistant"]
        if assistant_msgs:
            prev_question = assistant_msgs[-1]["content"]

        if is_new_question:
            state.question_count += 1
            state.follow_ups_count = 0
            if state.interview_plan and day is not None:
                try:
                    day_int = int(day)
                    if day_int in state.interview_plan:
                        state.current_topic_idx = state.interview_plan.index(day_int)
                except Exception:
                    pass
        else:
            state.follow_ups_count += 1

        if meta and meta.get("hedging_detected"):
            state.hedging_count += 1

        # Check for hedging/overconfidence mismatch
        mismatch_flag = "aligned"
        if meta:
            correctness = meta.get("correctness")
            confidence = meta.get("confidence")
            if correctness is not None and confidence is not None:
                if correctness <= 2 and confidence >= 4:
                    mismatch_flag = "overconfident"
                elif correctness >= 4 and confidence <= 2:
                    mismatch_flag = "hedging"

        if meta:
            state.performance_log.append({
                "turn": state.question_count,
                "day": day,
                "clarity": meta.get("clarity"),
                "confidence": meta.get("confidence"),
                "correctness": meta.get("correctness"),
                "gap_type": meta.get("gap_type", "none"),
                "hedging_detected": bool(meta.get("hedging_detected", False)),
                "recitation_flag": meta.get("recitation_flag", "explained"),
                "recitation_reason": meta.get("recitation_reason", ""),
                "similarity_score": meta.get("similarity_score", 0.0),
                "mismatch_flag": mismatch_flag,
                "reasoning_trace": meta.get("reasoning_trace", ""),
                "question": prev_question,
                "answer": user_message or "Kickoff started."
            })

        # Curveball injection checker (once >= 4 days covered and question count >= 6)
        if len(state.days_covered) >= 4 and state.question_count >= 6:
            state.inject_curveball = True

        # Now persist only the clean user message and model reply in history
        if kickoff:
            state.history.append({
                "role": "user",
                "content": "Please begin the interview: greet the candidate briefly and ask your first question."
            })
        elif user_message is not None:
            state.history.append({
                "role": "user",
                "content": user_message
            })
        state.history.append({
            "role": "assistant",
            "content": reply
        })

        out = {
            "reply": reply,
            "done": False,
            "clarity": meta.get("clarity") if meta else None,
            "confidence": meta.get("confidence") if meta else None
        }

        if (wants_to_wrap and minimums_met) or state.question_count >= MAX_QUESTIONS:
            if feedback is None or not wants_to_wrap:
                # Safety cap hit, force wrap-up feedback
                feedback = self._force_feedback(state)
            state.done = True
            state.feedback = feedback
            out["done"] = True
            out["feedback"] = feedback
            if state.question_count >= MAX_QUESTIONS and not wants_to_wrap:
                out["reply"] = reply or "That's a great place to stop -- thanks for walking me through your work."

        self._save_sessions()
        return out

    def _progress_summary(self, state: SessionState) -> str:
        plan_desc = ", ".join(f"Day {d}" for d in state.interview_plan)
        return (
            f"STRUCTURED INTERVIEW STATE:\n"
            f"- Structured Interview Plan (prioritized target days): [{plan_desc}]\n"
            f"- Current Target Index in Plan: {state.current_topic_idx} (Target Day: {state.interview_plan[state.current_topic_idx] if state.interview_plan and state.current_topic_idx < len(state.interview_plan) else 'None'})\n"
            f"- Current Topic Follow-Ups Count: {state.follow_ups_count}\n"
            f"- Total Hedging Count Detected: {state.hedging_count}\n"
            f"- Questions asked so far: {state.question_count} (minimum required: {MIN_QUESTIONS}).\n"
            f"- Distinct curriculum days probed so far: {sorted(state.days_covered)} "
            f"({len(state.days_covered)} of the minimum {MIN_DAYS} required).\n"
            f"You may end the interview once BOTH minimums are met and you feel you have "
            f"enough signal on the candidate's understanding. Do not end before both minimums are met."
        )

    def _system_prompt(self, state: SessionState) -> str:
        member = state.candidate.get("member", {})
        missions = state.candidate.get("missions", [])
        signals = state.candidate.get("signals", {})

        completed = [m for m in missions if m.get("passed")]
        skipped = [m for m in missions if m.get("skipped")]
        failed = [m for m in missions if m.get("passed") is False]

        candidate_block = json.dumps(
            {
                "name": member.get("name"),
                "jobRole": member.get("jobRole"),
                "yearsExperience": member.get("yearsExperience"),
                "education": member.get("education"),
                "signals": signals,
                "completed_missions": [
                    {"day": m["day"], "title": m["title"], "attempts": m.get("attempts")}
                    for m in completed
                ],
                "skipped_missions": [{"day": m["day"], "title": m["title"]} for m in skipped],
                "failed_missions": [
                    {"day": m["day"], "title": m["title"], "attempts": m.get("attempts")} for m in failed
                ],
            },
            indent=2,
        )

        relevant_days = {m["day"] for m in missions}
        curriculum_block = json.dumps(
            [
                {
                    "day": d["day"],
                    "title": d["title"],
                    "type": d.get("type"),
                    "tools": d.get("tools"),
                    "objectives": d.get("objectives"),
                }
                for d in CURRICULUM["days"]
                if d["day"] in relevant_days
            ],
            indent=2,
        )

        curveball_alert = ""
        if getattr(state, "inject_curveball", False):
            curveball_alert = (
                f"\nALERT -- CURVEBALL TRIGGERED:\n"
                f"- The candidate has covered at least 4 distinct topic domains and asked 6+ questions.\n"
                f"- On this turn, you MUST ask a cross-topic curveball question that forces the candidate "
                f"to connect two distinct curriculum areas (e.g. how RAG chunk ingestion metadata filters "
                f"relate to Model Context Protocol tool execution nodes under production deployment setups).\n"
                f"- Integrate this cross-topic curveball into your reply organically."
            )

        rag_context = ""
        if state.history and len(state.history) > 1:
            rag_context = (
                f"\nREAL-TIME TURN RAG EVALUATION:\n"
                f"- Target Day Curriculum Objective: {getattr(state, 'last_turn_objective', 'N/A')}\n"
                f"- Candidate Last Answer Similarity Score to Objective: {getattr(state, 'last_turn_similarity', 0.0):.2f}\n"
                f"  (Note: Scores > 0.45 indicate the candidate's response is highly similar to the curriculum textbook objectives -- "
                f"they might be rote-reciting or copy-pasting definition phrases. Fact check if they genuinely explain the choices.)"
            )

        return f"""You are a senior technical interviewer conducting a live, spoken-style technical interview \
for a candidate who just completed "{CURRICULUM['cohort']}", an enterprise AI engineering program.

{curveball_alert}
{rag_context}

CANDIDATE PROFILE AND LEARNING SIGNALS
{candidate_block}

CURRICULUM CONTEXT FOR DAYS THIS CANDIDATE ACTUALLY WORKED ON
(only ask about topics that appear here -- they are the only ones the candidate covered)
{curriculum_block}

INTERVIEW OBJECTIVE
Assess how well the candidate actually understands the systems they built and the engineering
decisions behind them -- not whether they memorized the curriculum. Favor questions that reveal
reasoning: "why did you choose X over Y", "what would break if Z", "walk me through what happens when...".

HOW TO CHOOSE WHAT TO ASK
- Only ask about days present in the curriculum context above (topics the candidate completed).
- Prioritize signal: days with many attempts (they struggled -- probe whether they now understand
  the concept or just brute-forced the mission), days completed first-try (verify depth, not luck),
  and days central to their stated job role.
- Cover at least {MIN_DAYS} distinct curriculum days across the interview, spanning different modules
  where possible (don't cluster all questions in one topic area).
- It is fine to briefly ask the candidate to reflect on a SKIPPED topic (e.g. "you skipped the
  fine-tuning mission -- do you have a sense of when you'd reach for fine-tuning vs. RAG?") as one
  of your questions, since that's diagnostic too.

HOW TO CONDUCT THE INTERVIEW
- One question at a time. Process-driven, professional, conversational interviewer tone -- not a quiz.
- WARM-UP RULE: On kickoff (first question), ask a warm-up project overview question instead of a curriculum day topic.
- DIFFICULTY RULE: Automatically raise question technical difficulty and depth (e.g. detailed internal lock contention, vector serialization) if candidate scored high (average score >= 4) in previous turns. Lower it to target base concept explanations if they scored low (average score <= 2).
- REASONING-DRIVEN FOLLOW-UPS: Every time the candidate answers, analyze the gap in their understanding:
  - If their response is SHALLOW or NAME-DROPPING without explaining mechanics, push back: ask them to explain how the tool works under load or defend their architectural choices.
  - If their response is VAGUE, ask for concrete specifications (e.g. chunk overlaps, similarity thresholds).
  - If their response is WRONG or CONTRADICTORY, challenge them politely to reconcile it with cohort curriculum facts.
  - If their response has NO GAPS ("none"), or if you've already asked 2 follow-ups on the current day, make a natural, organic transition to the next curriculum topic in the interview plan.
- Never ask more than one new question in a single reply.
- Keep each message reasonably short (a few sentences), like a real interviewer would type/say.

PROGRESS SO FAR
{self._progress_summary(state)}

WHEN TO END
Once you have asked at least {MIN_QUESTIONS} substantive questions AND covered at least {MIN_DAYS}
distinct curriculum days, and you feel you have enough signal, wrap up warmly in your `reply` (thank
them, no new question) and set "done": true with a populated "feedback" object. Do not end earlier.

OUTPUT FORMAT -- CRITICAL
Respond with ONLY a single valid JSON object and nothing else (no markdown fences, no commentary
before or after). Schema:

{{
  "reply": "<the exact text to show the candidate right now>",
  "done": <true only on the final message, else false>,
  "meta": {{
    "day": <the curriculum day number this message's question/follow-up is primarily about, or null if this message asks no new technical question (e.g. pure wrap-up)>,
    "is_new_question": <true if this message introduces a NEW question, false if it is a follow-up on the previous question or is not a question at all>,
    "clarity": <real-time rating of the candidate's response clarity, integer from 1 to 5, or null if kickoff>,
    "confidence": <real-time rating of the candidate's confidence/technical depth, integer from 1 to 5, or null if kickoff>,
    "correctness": <real-time rating of correctness against curriculum facts, integer from 1 to 5, or null if kickoff>,
    "gap_type": "<one of: 'none', 'vague', 'shallow', 'wrong', 'name_dropping'>",
    "hedging_detected": <true if candidate used hedging language like 'I think', 'maybe', 'not sure', else false>,
    "recitation_flag": "<'recited' if candidate verbatim copied text objectives, 'explained' if they used their own words>",
    "recitation_reason": "<a short explanation why>",
    "similarity_score": <similarity score from prompt context, or null if kickoff>,
    "reasoning_trace": "<a concise 1-2 sentence monospace trace detailing: current day target, personalization prioritization reasons, answer quality evaluation, and next-turn strategy>"
  }},
  "feedback": null unless "done" is true, in which case:
  {{
    "summary": "<2-4 sentence overall assessment>",
    "strengths": [
      "<highly detailed, evidence-based strength pointing to specific technical explanations given by the candidate>", 
      "..."
    ],
    "gaps": [
      "<highly detailed, evidence-based gap in conceptual understanding with concrete examples from their answers>", 
      "..."
    ],
    "next": [
      "<highly detailed, concrete, actionable next step for self-study and architecture improvements>", 
      "..."
    ],
    "skills": {{
      "Retrieval-Augmented Generation": <score from 0 to 100 based on answers in this interview>,
      "Vector Databases": <score from 0 to 100 based on answers in this interview>,
      "Prompt Engineering": <score from 0 to 100 based on answers in this interview>,
      "Agentic AI": <score from 0 to 100 based on answers in this interview>,
      "Production Systems": <score from 0 to 100 based on answers in this interview>
    }},
    "score": <overall percentage score, integer from 0 to 100>,
    "grade": "<overall letter grade, e.g. A, B+, B, C->",
    "status": "<overall recommendation status, must be one of: 'Strong Hire', 'Hire', 'Conditional Hire', 'Further Review'>",
    "overall_readiness": "<one of: 'Strong', 'Needs Practice', 'Not Ready'>",
    "communication_score": <overall communication capability rating, integer from 1 to 10>,
    "strong_topics": ["<major topic names candidate excelled at>", "..."],
    "recommended_review": ["Day <day_number>", "..."],
    "sample_ideal_answer": "<a comprehensive model answer combining RAG, vector databases, prompt techniques, and production engineering>",
    "topic_breakdown": [
      {{
        "day": <curriculum day number>,
        "topic": "<topic title>",
        "score": <score from 0 to 10, integer>,
        "evidence": "<concrete evidence details from candidate's responses during this interview>",
        "gap": "<specific gap description, or null if fully understood>"
      }},
      ...
    ]
  }}
}}

Base "feedback" strictly on how the candidate actually answered during THIS interview, not on their
attempt counts alone -- attempt counts are only a hint for what to probe."""

    def _call_model(self, state: SessionState, user_message: Optional[str], kickoff: bool):
        if getattr(state, "mock", False):
            from .mock_script import SCRIPT
            idx = getattr(state, "mock_index", 0)
            if idx < len(SCRIPT):
                item = SCRIPT[idx]
                state.mock_index = idx + 1
                reply = item["reply"]
                meta = item["meta"]
                feedback = item["feedback"]
                if item.get("done") is not True:
                    feedback = None
                return reply, meta, feedback
            else:
                return "The mock session is complete.", {"day": None, "is_new_question": False}, None

        # --- RAG GROUNDING & RECITATION SIMILARITY ---
        similarity_score = 0.0
        rag_objective = "Assess general technical understanding."
        current_day = 7
        
        # Extract current target day from planned interview plan
        if state.interview_plan and state.current_topic_idx < len(state.interview_plan):
            current_day = state.interview_plan[state.current_topic_idx]
            curr_day_data = get_curriculum_day(current_day)
            rag_objective = curr_day_data.get("objectives", "Understand core concepts.")

        # Compare candidate's answer against the target day objective
        if user_message:
            try:
                similarity_score = VECTOR_STORE.compute_similarity(user_message, rag_objective)
            except Exception:
                pass

        # Expose similarity to system instructions
        state.last_turn_similarity = similarity_score
        state.last_turn_objective = rag_objective

        try:
            system = self._system_prompt(state)

            messages = list(state.history)
            if kickoff:
                messages.append(
                    {
                        "role": "user",
                        "content": "Please begin the interview: greet the candidate briefly and ask your first question.",
                    }
                )
            elif user_message is not None:
                messages.append({"role": "user", "content": user_message})

            # Check if the client is mocked (e.g. in test_agent_smoke.py)
            if hasattr(self, "client") and self.client is not None and not isinstance(self.client, anthropic.Anthropic):
                response = self.client.messages.create(
                    model=MODEL,
                    max_tokens=1000,
                    system=system,
                    messages=messages,
                )
                raw_text = "".join(block.text for block in response.content if block.type == "text")
            else:
                raw_text = self.llm_service.generate_reply(system, messages)

            reply, meta, feedback = self._parse_model_json(raw_text)
            
            # Write similarity and recitation flags
            if meta:
                meta["similarity_score"] = float(f"{similarity_score:.2f}")
                if "recitation_flag" not in meta:
                    meta["recitation_flag"] = "recited" if similarity_score > 0.45 else "explained"
                    meta["recitation_reason"] = "Generated from backend TF-IDF Cosine check."
                    
            return reply, meta, feedback

        except Exception as e:
            # Graceful Fallback Turn Generation
            fallback_reply = f"Let's move to a different area -- walk me through your technical reasoning for Day {current_day} ({DAYS_BY_NUMBER.get(current_day, {}).get('title', 'Core RAG')})."
            fallback_meta = {
                "day": current_day,
                "is_new_question": True,
                "clarity": 3,
                "confidence": 3,
                "correctness": 3,
                "gap_type": "none",
                "hedging_detected": False,
                "recitation_flag": "explained",
                "recitation_reason": f"Fallback turn generated due to live API call failure: {e}",
                "similarity_score": 0.0,
                "reasoning_trace": f"System Alert: Graceful fallback active. API error: {e}. Transitioned to Day {current_day}."
            }
            return fallback_reply, fallback_meta, None

    @staticmethod
    def _parse_model_json(raw_text: str):
        text = raw_text.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if not match:
                return text, {"day": None, "is_new_question": False}, None
            try:
                data = json.loads(match.group(0))
            except Exception:
                return text, {"day": None, "is_new_question": False}, None

        reply = data.get("reply", "")
        meta = data.get("meta") or {}
        feedback = data.get("feedback")
        
        # Pull clarity and confidence if model outputs them at root level
        if "clarity" in data and "clarity" not in meta:
            meta["clarity"] = data["clarity"]
        if "confidence" in data and "confidence" not in meta:
            meta["confidence"] = data["confidence"]

        if data.get("done") is not True:
            feedback = None
        return reply, meta, feedback

    def _force_continue(self, state: SessionState, user_message: Optional[str], kickoff: bool, premature_reply: str):
        """Called when the model tries to wrap up before minimums are met."""
        if getattr(state, "mock", False):
            return self._call_model(state, user_message, kickoff)

        remaining_days = MIN_DAYS - len(state.days_covered)
        nudge = (
            f"You have not yet met the interview minimums "
            f"({state.question_count}/{MIN_QUESTIONS} questions, {len(state.days_covered)}/{MIN_DAYS} distinct days). "
            f"Do not wrap up yet. Ask exactly one more substantive NEW question"
            + (f", ideally about a curriculum day not yet covered ({remaining_days} more distinct day(s) needed)"
               if remaining_days > 0 else "")
            + '. Respond with ONLY the JSON envelope, "done": false, "feedback": null.'
        )

        temp_messages = list(state.history)
        if kickoff:
            temp_messages.append({
                "role": "user",
                "content": "Please begin the interview: greet the candidate briefly and ask your first question."
            })
        elif user_message is not None:
            temp_messages.append({"role": "user", "content": user_message})

        # Append rejected wrap-up and the system's instruction nudge
        temp_messages.append({"role": "assistant", "content": premature_reply})
        temp_messages.append({"role": "user", "content": nudge})

        system = self._system_prompt(state)

        if hasattr(self, "client") and self.client is not None and not isinstance(self.client, anthropic.Anthropic):
            response = self.client.messages.create(
                model=MODEL,
                max_tokens=1000,
                system=system,
                messages=temp_messages,
            )
            raw_text = "".join(block.text for block in response.content if block.type == "text")
        else:
            raw_text = self.llm_service.generate_reply(system, temp_messages)

        reply, meta, feedback = self._parse_model_json(raw_text)
        return reply, meta, feedback

    def _force_feedback(self, state: SessionState) -> dict:
        """Called only if MAX_QUESTIONS is hit without the model wrapping up itself."""
        if getattr(state, "mock", False):
            from .mock_script import SCRIPT
            return SCRIPT[-1]["feedback"]

        wrap_prompt = (
            "We're at the question limit for this interview. Do not ask anything further. "
            'Respond with ONLY the JSON envelope, with "done": true, "reply" containing a short '
            'warm closing line, and a fully populated "feedback" object based on the conversation so far.'
        )
        temp_messages = list(state.history) + [{"role": "user", "content": wrap_prompt}]
        system = self._system_prompt(state)

        if hasattr(self, "client") and self.client is not None and not isinstance(self.client, anthropic.Anthropic):
            response = self.client.messages.create(
                model=MODEL,
                max_tokens=800,
                system=system,
                messages=temp_messages,
            )
            raw_text = "".join(block.text for block in response.content if block.type == "text")
        else:
            raw_text = self.llm_service.generate_reply(system, temp_messages)

        _, _, feedback = self._parse_model_json(raw_text)
        if feedback is None:
            feedback = {
                "summary": "Interview concluded after reaching the maximum question count.",
                "strengths": ["Completed the assessment timeline and covered RAG, Agentic, and Production modules."],
                "gaps": ["Review of failure states and retry policies under connection loss or throttling."],
                "next": ["Perform structured self-study on production monitoring and logging tools."],
                "skills": {
                    "Retrieval-Augmented Generation": 60,
                    "Vector Databases": 60,
                    "Prompt Engineering": 60,
                    "Agentic AI": 60,
                    "Production Systems": 60
                },
                "score": 60,
                "grade": "C-",
                "status": "Further Review",
                "overall_readiness": "Needs Practice",
                "communication_score": 6,
                "strong_topics": ["Retrieval-Augmented Generation"],
                "recommended_review": ["Day 22"],
                "sample_ideal_answer": "Focus on production monitoring, rate-limiting handlers, and multi-agent coordination states.",
                "topic_breakdown": [
                    {
                        "day": 22,
                        "topic": "Agentic AI",
                        "score": 6,
                        "evidence": "Completed the general timeline, but lacked deep failure mitigation strategies.",
                        "gap": "Weak exception handling when agents timeout."
                    }
                ]
            }
        return feedback
