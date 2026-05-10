"""
Feedback & Coaching Agent (Agent 6)
Generates structured, actionable feedback using Groq, falls back to heuristic rules.
"""

from ..services.groq_client import groq_json


async def generate_feedback_async(metrics: dict, questions: list, answers: list, adaptation_log: list) -> dict | None:
    answers_text = "\n".join([
        f"Q: {questions[i]['text'][:100] if i < len(questions) else 'N/A'}\nA: {a[:300]}"
        for i, a in enumerate(answers)
    ])
    prompt = (
        f"Interview Performance Data:\n"
        f"- Technical Score: {metrics.get('technicalScore', 0)}/99\n"
        f"- Communication Score: {metrics.get('communicationScore', 0)}/99\n"
        f"- Confidence Score: {metrics.get('confidenceScore', 0)}/99\n"
        f"- Engagement Score: {metrics.get('engagementScore', 0)}/99\n"
        f"- Depth of Knowledge: {metrics.get('depthOfKnowledge', 0)}/99\n"
        f"- Stress Level: {metrics.get('stressLevel', 0)}/99\n\n"
        f"Adaptation Log:\n{chr(10).join(adaptation_log)}\n\n"
        f"Q&A Samples:\n{answers_text[:2000]}\n\n"
        f"Generate structured post-interview feedback."
    )
    return await groq_json("feedback_generator", prompt, temperature=0.4, max_tokens=1500)


def generate_feedback(metrics: dict, questions: list, answers: list, adaptation_log: list) -> dict:
    strengths = []
    improvements = []
    technical_gaps = []
    communication_tips = []
    behavioral_insights = []

    tech_score = metrics.get("technicalScore", 0)
    comm_score = metrics.get("communicationScore", 0)
    conf_score = metrics.get("confidenceScore", 0)
    engagement = metrics.get("engagementScore", 0)
    depth = metrics.get("depthOfKnowledge", 0)

    if tech_score >= 70:
        strengths.append("Strong technical fundamentals and problem-solving approach")
    if comm_score >= 70:
        strengths.append("Clear and well-structured communication")
    if conf_score >= 70:
        strengths.append("High vocal confidence and steady delivery")
    if engagement >= 70:
        strengths.append("Strong engagement and positive presence")
    if depth >= 70:
        strengths.append("Deep knowledge demonstrated across topics")
    if tech_score >= 60 and tech_score < 70:
        strengths.append("Solid technical foundation with room to deepen")
    if comm_score >= 60 and comm_score < 70:
        strengths.append("Good communication; minor room for improvement")

    if tech_score < 60:
        improvements.append("Strengthen core technical concepts through structured practice")
        technical_gaps.append("Core concept coverage needs expansion")
    if depth < 50:
        improvements.append("Go deeper into each topic rather than surface-level coverage")
        technical_gaps.append("Depth of knowledge — probe beyond definitions into tradeoffs")
    if depth < 70 and tech_score >= 60:
        improvements.append("Add more technical depth and specifics to your answers")
        technical_gaps.append("Technical depth — include benchmarks, tradeoffs, and real examples")
    if comm_score < 60:
        improvements.append("Structure your answers more clearly (use frameworks like STAR)")
        communication_tips.append("Use the STAR method (Situation, Task, Action, Result) for behavioral questions")
    if conf_score < 60:
        improvements.append("Work on vocal delivery — slow down and reduce filler words")
        communication_tips.append("Practice pausing instead of using filler words (um, like, you know)")
    if engagement < 60:
        improvements.append("Improve eye contact and positive body language")
        behavioral_insights.append("Your engagement level suggests room for more confident body language")
    if conf_score < 50:
        improvements.append("Build confidence through repeated mock interview practice")
    if tech_score < 50:
        technical_gaps.append("Systematic approach to problem-solving — practice with a structured methodology")

    if comm_score < 70:
        communication_tips.append("Slow down your speaking pace — aim for 130-150 words per minute")
        communication_tips.append("Pause briefly between key points to let them land")
    if conf_score < 70:
        communication_tips.append("Record yourself and review for filler word patterns")

    for log in adaptation_log:
        if "struggling" in log.lower():
            behavioral_insights.append("The system detected struggling patterns — focus on fundamentals before advancing")
        if "excelling" in log.lower():
            behavioral_insights.append("The system detected strong performance — consider tackling harder challenges")
        if "encouragement" in log.lower():
            behavioral_insights.append("The system detected low confidence and provided encouragement — building self-assurance will help")
        if "performing well" in log.lower():
            behavioral_insights.append("The system recognized strong performance and increased depth accordingly")

    avg_score = (tech_score + comm_score + conf_score + engagement) / 4

    if not strengths:
        strengths.append("Good effort — consistent practice will build mastery")
    if not improvements:
        improvements.append("Maintain your current preparation routine")
    if not technical_gaps:
        technical_gaps.append("No significant technical gaps detected")
    if not communication_tips:
        communication_tips.append("Your communication style is effective")
    if not behavioral_insights:
        behavioral_insights.append("Good behavioral response patterns")

    return {
        "strengths": strengths[:4],
        "improvements": improvements[:4],
        "technicalGaps": technical_gaps[:3],
        "communicationTips": communication_tips[:4],
        "behavioralInsights": behavioral_insights[:3],
        "overallScore": int(avg_score),
    }
