"""
Technical Evaluation Engine (Agent 5)
Evaluates answers using Groq for semantic scoring, falls back to keyword matching.
"""

import re
from ..services.groq_client import groq_json

TECHNICAL_KEYWORDS: dict[str, list[str]] = {
    "system_design": ["scalability", "microservices", "load balancing", "caching", "database",
                      "consistency", "availability", "partition tolerance", "latency", "throughput",
                      "replication", "sharding", "message queue", "cd", "cdn", "api gateway"],
    "frontend": ["component", "state", "props", "hook", "virtual dom", "rendering",
                 "performance", "lazy loading", "bundle", "responsive", "accessibility",
                 "css", "animation", "event loop", "closure", "promise"],
    "backend": ["api", "rest", "graphql", "database", "query", "index", "transaction",
                "authentication", "authorization", "middleware", "webhook", "rate limiting",
                "error handling", "logging", "monitoring", "async", "worker"],
    "algorithms": ["time complexity", "space complexity", "dynamic programming", "recursion",
                   "binary search", "graph", "tree", "sort", "hash", "array",
                   "optimization", "brute force", "divide and conquer", "greedy"],
    "behavioral": ["leadership", "ownership", "collaboration", "mentor", "conflict",
                   "deadline", "stakeholder", "initiative", "impact", "team",
                   "challenge", "solution", "result", "learn", "improve"],
}


async def evaluate_answer_async(question: str, answer: str, question_type: str) -> dict | None:
    if not answer.strip():
        return None
    prompt = (
        f"Question ({question_type}): {question}\n\n"
        f"Candidate Answer: {answer}\n\n"
        f"Evaluate thoroughly per the evaluation rubric."
    )
    result = await groq_json("answer_evaluator", prompt, temperature=0.2, max_tokens=800)
    if result and "correctnessScore" in result:
        return result
    fallback = evaluate_answer_heuristic(question, answer, question_type)
    fallback["internal_monologue"] = "Groq unavailable; used heuristic evaluation."
    return fallback


def evaluate_answer_heuristic(question: str, answer: str, question_type: str) -> dict:
    if not answer.strip():
        return {"correctnessScore": 0, "depthOfKnowledge": 0, "feedback": "No answer provided.", "matchedKeywords": [], "weaknesses": ["No answer provided"], "missingConcepts": [], "strengths": [], "drill_down_topic": ""}

    q_lower = question.lower()
    a_lower = answer.lower()

    domain_key = question_type.replace("-", "_")
    if domain_key not in TECHNICAL_KEYWORDS:
        domain_key = "backend"

    keywords = TECHNICAL_KEYWORDS.get(domain_key, TECHNICAL_KEYWORDS["backend"])

    matched_keywords = []
    for kw in keywords:
        if kw.lower() in a_lower:
            matched_keywords.append(kw)

    keyword_match_ratio = len(matched_keywords) / max(len(keywords) * 0.2, 1)
    keyword_score = min(keyword_match_ratio * 100, 80)

    answer_length = len(answer.split())
    length_score = min(answer_length / 20 * 30, 30) if answer_length >= 10 else max(answer_length / 10 * 15, 5)

    structure_indicators = ["first", "second", "finally", "in conclusion", "for example", "specifically", "in addition", "moreover"]
    structure_score = sum(1 for w in structure_indicators if w in a_lower) * 5

    relevance = 0
    q_keywords = set(re.findall(r'\b\w+\b', q_lower)) - {'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'and', 'or', 'is', 'are'}
    a_keywords = set(re.findall(r'\b\w+\b', a_lower))
    common = q_keywords & a_keywords
    if q_keywords:
        relevance = len(common) / len(q_keywords) * 20

    correctnessScore = int(min(keyword_score + relevance + structure_score, 99))
    depthOfKnowledge = int(min(len(matched_keywords) * 8 + min(answer_length / 30 * 15, 25), 99))

    if len(matched_keywords) >= 5:
        feedback = "Strong technical depth with relevant concepts covered."
    elif len(matched_keywords) >= 3:
        feedback = "Good coverage of key concepts. Consider adding more depth."
    else:
        feedback = "Surface-level coverage. Try structuring your answer with specific technical details."

    if structure_score >= 10:
        feedback += " Well-structured response."

    weaknesses = []
    missingConcepts = []
    strengths = list(matched_keywords[:3])
    drill_down_topic = ""

    if depthOfKnowledge < 40:
        weaknesses.append("Answer lacked depth — consider explaining trade-offs and internals")
        drill_down_topic = f"deeper exploration of {', '.join(keywords[:3])}"
    if len(matched_keywords) < 3:
        weaknesses.append("Few domain-specific keywords covered")
        missingConcepts = [kw for kw in keywords[:5] if kw not in a_lower]
    if answer_length < 30:
        weaknesses.append("Answer was too brief")
    if answer_length > 150 and len(matched_keywords) < 3:
        weaknesses.append("Answer was verbose but lacked technical substance")

    return {
        "correctnessScore": correctnessScore,
        "depthOfKnowledge": depthOfKnowledge,
        "matchedKeywords": matched_keywords[:8],
        "feedback": feedback,
        "weaknesses": weaknesses,
        "missingConcepts": missingConcepts,
        "strengths": strengths,
        "drill_down_topic": drill_down_topic,
    }


def evaluate_answer(question: str, answer: str, question_type: str) -> dict:
    return evaluate_answer_heuristic(question, answer, question_type)
