# Pre-defined script of questions and feedback for offline demonstration.
SCRIPT = [
    {
        "reply": "Welcome! Before we dive into the technical details, give me a quick 30-second overview of the Capstone project you built for this cohort.",
        "done": False,
        "meta": {
            "day": None,
            "is_new_question": True,
            "clarity": 5,
            "confidence": 5,
            "correctness": 5,
            "gap_type": "none",
            "hedging_detected": False,
            "recitation_flag": "explained",
            "recitation_reason": "Introduction warm-up question.",
            "similarity_score": 0.0,
            "reasoning_trace": "Interviewer Agent Action: Initiating evaluation loop. Asking a friendly warm-up project overview question to establish conversational tone."
        },
        "feedback": None
    },
    {
        "reply": "Great project! Let's start with Day 7 RAG concepts -- tell me how you designed your embedding pipeline.",
        "done": False,
        "meta": {
            "day": 7,
            "is_new_question": True,
            "clarity": 4,
            "confidence": 4,
            "correctness": 4,
            "gap_type": "none",
            "hedging_detected": False,
            "recitation_flag": "explained",
            "recitation_reason": "Provided custom description of embeddings design.",
            "similarity_score": 0.28,
            "reasoning_trace": "Interviewer Agent Action: Targeting Day 7. Initiating RAG embedding question. Reason: Chen has skipped Day 7. Checking basic pipeline structures."
        },
        "feedback": None
    },
    {
        "reply": "Got it. Follow-up: why that chunking strategy specifically?",
        "done": False,
        "meta": {
            "day": 7,
            "is_new_question": False,
            "clarity": 4,
            "confidence": 3,
            "correctness": 4,
            "gap_type": "none",
            "hedging_detected": True,
            "recitation_flag": "explained",
            "recitation_reason": "Answered correctly in own words.",
            "similarity_score": 0.25,
            "reasoning_trace": "Interviewer Agent Action: Asking follow-up on Day 7. Reason: Candidate used hedging terms ('I think', 'maybe'). Probing underlying architectural logic."
        },
        "feedback": None
    },
    {
        "reply": "Makes sense. Next -- walk me through your retrieval routing logic.",
        "done": False,
        "meta": {
            "day": 10,
            "is_new_question": True,
            "clarity": 5,
            "confidence": 4,
            "correctness": 5,
            "gap_type": "none",
            "hedging_detected": False,
            "recitation_flag": "explained",
            "recitation_reason": "Detailed metadata mapping logic clearly.",
            "similarity_score": 0.32,
            "reasoning_trace": "Interviewer Agent Action: Transitioning to Day 10. Prioritizing: Chen has 4 attempts on Day 10 matching engines. Probing if they grasp metadata filters."
        },
        "feedback": None
    },
    {
        "reply": "How did you design your multi-agent handoff?",
        "done": False,
        "meta": {
            "day": 22,
            "is_new_question": True,
            "clarity": 4,
            "confidence": 5,
            "correctness": 4,
            "gap_type": "none",
            "hedging_detected": False,
            "recitation_flag": "explained",
            "recitation_reason": "Described routers using custom diagrams terminology.",
            "similarity_score": 0.29,
            "reasoning_trace": "Interviewer Agent Action: Transitioning to Day 22 Agentic AI. Prioritizing: Chen skipped Day 22. Checking multi-agent state coordination logic."
        },
        "feedback": None
    },
    {
        "reply": "What would break if one agent timed out mid-handoff?",
        "done": False,
        "meta": {
            "day": 22,
            "is_new_question": False,
            "clarity": 3,
            "confidence": 5,
            "correctness": 2,
            "gap_type": "shallow",
            "hedging_detected": False,
            "recitation_flag": "recited",
            "recitation_reason": "verbatim copied the curriculum recovery text instead of explaining the failure recovery logic.",
            "similarity_score": 0.65,
            "reasoning_trace": "Interviewer Agent Action: Probing Day 22. Detected: Overconfident/Recited response (Correctness: 2, Confidence: 5, Similarity: 0.65). Copied textbook definition without explaining timeout handlers."
        },
        "feedback": None
    },
    {
        "reply": "Tell me about your MCP server -- what tools did it expose?",
        "done": False,
        "meta": {
            "day": 23,
            "is_new_question": True,
            "clarity": 4,
            "confidence": 4,
            "correctness": 4,
            "gap_type": "none",
            "hedging_detected": False,
            "recitation_flag": "explained",
            "recitation_reason": "Outlined custom exposed resources correctly.",
            "similarity_score": 0.31,
            "reasoning_trace": "Interviewer Agent Action: Moving to Day 23 Model Context Protocol. Chen completed Day 23 on first attempt. Checking tool schemas integration."
        },
        "feedback": None
    },
    {
        "reply": "One more -- how did you containerize the deployment?",
        "done": False,
        "meta": {
            "day": 28,
            "is_new_question": True,
            "clarity": 4,
            "confidence": 4,
            "correctness": 4,
            "gap_type": "none",
            "hedging_detected": False,
            "recitation_flag": "explained",
            "recitation_reason": "Explained container building steps.",
            "similarity_score": 0.22,
            "reasoning_trace": "Interviewer Agent Action: Transitioning to Day 28 Production Systems. Prioritizing: Chen skipped Day 28. Checking docker multi-stage compilation steps."
        },
        "feedback": None
    },
    {
        "reply": "And how are you monitoring it in production?",
        "done": False,
        "meta": {
            "day": 29,
            "is_new_question": True,
            "clarity": 5,
            "confidence": 4,
            "correctness": 4,
            "gap_type": "none",
            "hedging_detected": False,
            "recitation_flag": "explained",
            "recitation_reason": "Detailed Prometheus metrics and logging setup.",
            "similarity_score": 0.26,
            "reasoning_trace": "Interviewer Agent Action: Moving to Day 29 monitoring. Chen failed Day 29 twice. Verifying observability pipelines."
        },
        "feedback": None
    },
    {
        "reply": "One more -- how would your RAG pipeline's metadata filter interface with custom tools exposed by your MCP server?",
        "done": False,
        "meta": {
            "day": None,
            "is_new_question": True,
            "clarity": 4,
            "confidence": 5,
            "correctness": 5,
            "gap_type": "none",
            "hedging_detected": False,
            "recitation_flag": "explained",
            "recitation_reason": "Successfully connected RAG ingestion filters with MCP resource declarations.",
            "similarity_score": 0.38,
            "reasoning_trace": "Planner Agent Action: Triggering Curveball. Conditions met (>= 4 topics covered, question count >= 6). Asking cross-topic question connecting RAG and MCP tools."
        },
        "feedback": None
    },
    {
        "reply": "Last one -- what would you change about the architecture with more time?",
        "done": False,
        "meta": {
            "day": 31,
            "is_new_question": True,
            "clarity": 5,
            "confidence": 5,
            "correctness": 5,
            "gap_type": "none",
            "hedging_detected": False,
            "recitation_flag": "explained",
            "recitation_reason": "Shared detailed reflections on scaling.",
            "similarity_score": 0.18,
            "reasoning_trace": "Interviewer Agent Action: Final turn Day 31 Capstone. Probing overall architecture reflection and feedback."
        },
        "feedback": None
    },
    {
        "reply": "Thanks, that's everything I need -- appreciate you walking me through it.",
        "done": True,
        "meta": {
            "day": None,
            "is_new_question": False,
            "clarity": 5,
            "confidence": 5,
            "correctness": 5,
            "gap_type": "none",
            "hedging_detected": False,
            "recitation_flag": "explained",
            "recitation_reason": "Interview wrap-up.",
            "similarity_score": 0.0,
            "reasoning_trace": "Interviewer Agent Action: Minimum checks met (10 questions asked, 5 distinct days covered). Closing interview and compiling diagnostic feedback."
        },
        "feedback": {
            "summary": "Strong on systems thinking, thin on agent orchestration. Ready with one more pass on Day 22 Multi-Agent coordinates.",
            "strengths": [
                "Detailed knowledge of RAG embedding pipelines, specifically justifying semantic chunking sizes based on token costs and context window boundaries.",
                "Excellent structural design of metadata filtering and vector indexes, showing awareness of read/write query latency trade-offs.",
                "Strong comprehension of Model Context Protocol (MCP) server models, outlining tool structures and permission boundaries clearly."
            ],
            "gaps": [
                "Shallow reasoning regarding fallback strategies when coordinate agents time out mid-handoff.",
                "Vague explanation of production retry policies under rate-limiting (e.g. exponential backoff with jitter)."
            ],
            "next": [
                "Implement structured exception and timeout handling routines within the multi-agent router block.",
                "Review production monitoring metrics, focusing on latency percentiles and token throughput rates under high load."
            ],
            "skills": {
                "Retrieval-Augmented Generation": 90,
                "Vector Databases": 85,
                "Prompt Engineering": 80,
                "Agentic AI": 75,
                "Production Systems": 70
            },
            "score": 82,
            "grade": "A-",
            "status": "Strong Hire",
            "overall_readiness": "Strong",
            "communication_score": 9,
            "strong_topics": ["Retrieval-Augmented Generation", "Vector Databases"],
            "recommended_review": ["Day 22", "Day 29"],
            "sample_ideal_answer": "To design an airtight production agent pipeline, I would establish semantic chunking with a 200-token overlap to protect boundary intent, store vectors in Qdrant with HNSW indexes using payload metadata filters, and wrap agent delegation inside LangGraph state transition maps. I'd configure exponential backoff with jitter retry decorators for external API clients and output Pydantic-validated structures from our MCP servers.",
            "topic_breakdown": [
                {"day": 7, "topic": "Retrieval-Augmented Generation", "score": 9, "evidence": "Clearly explained chunking overlap trades and embeddings cost parameters.", "gap": None},
                {"day": 8, "topic": "Vector Databases", "score": 9, "evidence": "Defended HNSW read latency vs write cost structures correctly.", "gap": None},
                {"day": 22, "topic": "Agentic AI", "score": 7, "evidence": "Described specialist delegation maps, but lacked edge case recovery details.", "gap": "Vague exception handling when specialist node fails to return responses."},
                {"day": 23, "topic": "Model Context Protocol", "score": 8, "evidence": "Successfully mapped tool arrays and server definitions to schemas.", "gap": None},
                {"day": 29, "topic": "Production Systems", "score": 7, "evidence": "Laid out Prometheus metric pipelines, but didn't detail token rate limiting backups.", "gap": "Lacked specific backoff implementation under API throttling."}
            ]
        }
    }
]
