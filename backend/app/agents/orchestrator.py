"""
Interview Orchestrator Agent
Groq drives all question generation from full context.
No hardcoded text, templates, transitions, or encouragements.
"""

import uuid
from typing import Optional
from ..services.groq_client import groq_json
from .technical_evaluator import evaluate_answer
from .audio_intelligence import analyze_speech
from .visual_intelligence import analyze_video
from .feedback_agent import generate_feedback
from .interview_memory import (
    ConversationMemory,
    InterviewStateMachine,
    analyze_answer_depth,
    _extract_key_concepts,
)

DIFFICULTY_LEVELS = ["easy", "medium", "hard"]


class OrchestratorAgent:
    def __init__(self):
        self.memory = ConversationMemory()
        self.state_machine = InterviewStateMachine()
        self.performance_history: list[dict] = []
        self.current_difficulty: str = "medium"
        self.consecutive_struggles: int = 0
        self.consecutive_successes: int = 0
        self.encouragement_given: int = 0
        self.last_confidence: int = 70
        self.streak_scores: list[int] = []
        self._session_id: str = ""
        self._persona: str = "google"
        self._max_questions: int = 15

    @property
    def session_state(self) -> dict:
        return {
            "config": getattr(self, "_config", {}),
            "resume": getattr(self, "_resume", {}),
            "config": self._config,
            "questions_asked": self.memory.questions_asked,
            "answers_given": self.memory.answers_given,
            "conversation_history": self.memory.conversation_history,
            "scores": self.memory.scores,
            "adaptation_log": self.memory.adaptation_log,
            "encouragements": self.memory.encouragements,
        }

    @session_state.setter
    def session_state(self, value: dict):
        self._config = value.get("config", {})
        self._resume = value.get("resume", {})
        md = value.get("memory_dict")
        if md:
            self.memory = ConversationMemory.from_dict(md)
        smd = value.get("state_machine_dict")
        if smd:
            self.state_machine = InterviewStateMachine.from_dict(smd)
        self.current_difficulty = value.get("current_difficulty", "medium")
        self.consecutive_struggles = value.get("consecutive_struggles", 0)
        self.consecutive_successes = value.get("consecutive_successes", 0)
        self.encouragement_given = value.get("encouragement_given", 0)
        self.last_confidence = value.get("last_confidence", 70)
        self.streak_scores = value.get("streak_scores", [])
        self.performance_history = value.get("performance_history", [])
        self._persona = value.get("_persona", "google")
        self._max_questions = value.get("_max_questions", 15)

    def start_session(self, config: dict, resume_data: Optional[dict] = None) -> dict:
        self._config = config
        self._resume = resume_data or {}
        self.memory = ConversationMemory()
        self.state_machine = InterviewStateMachine()
        self.current_difficulty = self._map_difficulty(config.get("difficulty", "medium"))
        self.performance_history = []
        self.consecutive_struggles = 0
        self.consecutive_successes = 0
        self.encouragement_given = 0
        self.last_confidence = 70
        self.streak_scores = []
        self._session_id = str(uuid.uuid4())[:8]
        self._persona = config.get("persona", "google")
        return {"session_id": self._session_id, "status": "started"}

    def _map_difficulty(self, raw: str) -> str:
        m = {"beginner": "easy", "intermediate": "medium", "advanced": "hard"}
        return m.get(raw, raw if raw in DIFFICULTY_LEVELS else "medium")

    # ── Question Generation ──

    async def generate_question_async(self, previous_answer: Optional[str] = None) -> Optional[dict]:
        if len(self.memory.questions_asked) >= self._max_questions:
            return None
        config = self._config
        role = config.get("role", "Software Engineer")
        resume = self._resume or {}
        skills = resume.get("skills", [])
        projects = resume.get("projects", [])

        if previous_answer:
            self.memory.track_answer(previous_answer)
            depth_info = analyze_answer_depth(previous_answer)
            self.memory.track_answer_quality(depth_info["depth"])
            last_metrics = self.memory.scores[-1] if self.memory.scores else {"technicalScore": 50}
            if self.state_machine.should_transition(self.memory, last_metrics):
                old = self.state_machine.current_stage
                self.state_machine.advance()
                print(f"[Orchestrator] Stage: {old} -> {self.state_machine.current_stage}")

        stage_ctx = self.state_machine.get_context_for_prompt(self.memory)
        history = self.memory.conversation_history[-4:] if self.memory.conversation_history else []
        history_text = "\n".join(f"{m['role'].upper()}: {m['content'][:200]}" for m in history)
        asked = self.memory.questions_asked
        asked_text = "\n".join(
            f"- Q{i+1} ({q.get('topic','?')}, {q.get('difficulty','?')}): {q['text'][:100]}"
            for i, q in enumerate(asked[-3:])
        )

        last_answer_info = ""
        if previous_answer:
            depth_info = analyze_answer_depth(previous_answer)
            concepts = _extract_key_concepts(previous_answer)
            fc = self.memory.get_follow_up_context()
            weakness = self.memory.get_weakness_summary()
            extra = f"\n- Weaknesses to probe: {weakness}" if weakness and "no significant" not in weakness else ""
            last_answer_info = (
                f"Last answer analysis:\n"
                f"- Quality: {depth_info['depth'].upper()}, {depth_info['word_count']} words\n"
                f"- Signals: example={depth_info['has_example']}, metrics={depth_info['has_metrics']}, "
                f"tradeoffs={depth_info['has_tradeoffs']}, comparison={depth_info['has_comparison']}\n"
                f"- Concepts: {', '.join(list(concepts)[:8])}\n"
                f"- Probe depth: {fc['probe_depth']}/3 on this topic{extra}"
            )

        uncovered = self.memory.get_uncovered_topics()
        consecutive_note = ""
        if self.consecutive_struggles >= 2:
            consecutive_note = f"\nWARNING: Candidate struggling ({self.consecutive_struggles}x). Simplify questions."
        if self.consecutive_successes >= 2:
            consecutive_note = f"\nNOTE: Candidate excelling ({self.consecutive_successes}x). Ask harder questions."

        q_context = (
            f"Difficulty: {self.current_difficulty}{consecutive_note}\n"
            f"Role: {role} | Skills: {', '.join(skills[:6])}\n"
            f"Stage: {stage_ctx['stage']} — {stage_ctx['stage_description']}\n"
            f"Topics covered: {stage_ctx['topic_coverage'][:200]}\n"
            f"Uncovered: {', '.join(uncovered[:4]) if uncovered else 'All covered'}\n"
            f"Strengths: {stage_ctx['strengths'][:200]}\n"
            f"Weaknesses: {stage_ctx['weaknesses'][:200]}\n"
            f"Drill: {(stage_ctx.get('drill_recommendation') or '')[:100]}\n\n"
            f"{last_answer_info}\n"
            f"--- Questions asked (NEVER repeat) ---\n{asked_text}\n\n"
            f"--- Recent ---\n{history_text}\n\n"
            f"Generate the NEXT question. Follow system prompt."
        )

        result = await groq_json("question_generator", q_context, temperature=0.7, max_tokens=800)
        if result and "speech" in result:
            q_text = result["speech"]
            q_type = "technical"
            phase = result.get("phase", "")
            if "behavioral" in phase:
                q_type = "behavioral"
            elif "project" in phase:
                q_type = "project"
            topic = result.get("topic", "general")
            difficulty = result.get("difficulty", self.current_difficulty)
            question = {
                "id": f"q{len(self.memory.questions_asked) + 1}",
                "text": q_text,
                "type": q_type,
                "difficulty": difficulty,
                "internal_monologue": result.get("internal_monologue", ""),
                "phase": phase,
                "topic": topic,
                "is_drill_down": result.get("is_drill_down", False),
            }
            is_dup, _, _ = self.memory.is_duplicate(q_text)
            if is_dup:
                print(f"[Orchestrator] DEDUP")
                return None
            self.state_machine.stage_question_counts[self.state_machine.current_stage] += 1
            return question
        return None

    def generate_question(self, previous_answer: Optional[str] = None) -> Optional[dict]:
        if len(self.memory.questions_asked) >= self._max_questions:
            return None
        if not previous_answer:
            return None

        concepts = _extract_key_concepts(previous_answer)
        last_q = self.memory.questions_asked[-1] if self.memory.questions_asked else None
        last_topic = last_q.get("topic", "") if last_q else ""

        if concepts:
            words = list(concepts)[:2]
            text = f"Can you go deeper into how {' and '.join(words)} work together?"
        elif last_topic:
            text = f"Can you elaborate more on {last_topic.replace('_', ' ')}?"
        else:
            skills = (self._resume or {}).get("skills", [])
            if skills:
                text = f"Tell me more about your experience with {skills[0]}."
            else:
                return None

        self.state_machine.stage_question_counts[self.state_machine.current_stage] += 1
        return {"id": f"q{len(self.memory.questions_asked) + 1}", "text": text,
                "type": "technical", "difficulty": self.current_difficulty,
                "topic": last_topic or "general", "is_drill_down": True}

    # ── Answer Analysis ──

    def analyze_response(self, question_id: str, answer: str, transcript: str = "",
                         video_duration: float = 60.0,
                         groq_analysis: dict | None = None) -> dict:
        question = next((q for q in self.memory.questions_asked if q["id"] == question_id), None)
        if not question:
            return {"error": "Question not found", "metrics": self._default_metrics()}

        tech_eval = evaluate_answer(question["text"], answer, question["type"])
        depth_info = analyze_answer_depth(answer)
        if depth_info["depth"] in ("shallow", "minimal"):
            tech_eval["depthOfKnowledge"] = max(tech_eval["depthOfKnowledge"] - 15, 5)

        self.memory.track_answer(answer)
        self.memory.track_answer_quality(depth_info["depth"])
        audio = analyze_speech(transcript or answer, video_duration)
        visual = analyze_video(video_duration)

        if groq_analysis:
            for key in ("weaknesses", "missingConcepts", "strengths", "drill_down_topic",
                        "correctnessScore", "depthOfKnowledge", "feedback"):
                if key in groq_analysis:
                    tech_eval[key] = groq_analysis[key]

        metrics = {
            "technicalScore": tech_eval["correctnessScore"],
            "communicationScore": audio["communicationClarityScore"],
            "confidenceScore": audio["confidenceScore"],
            "engagementScore": visual["engagementScore"],
            "stressLevel": visual["stressLevel"],
            "depthOfKnowledge": tech_eval["depthOfKnowledge"],
        }

        self.last_confidence = metrics["confidenceScore"]
        self.memory.answers_given.append(answer)
        self.memory.scores.append(metrics)
        self.performance_history.append(metrics)
        self.memory.track_question(question, answer)
        self.memory.track_answer_analysis(tech_eval)
        self._adapt_difficulty(metrics, tech_eval, depth_info)

        return {
            "metrics": metrics,
            "feedback": tech_eval.get("feedback", ""),
            "transition": "",
            "adaptation": self.memory.adaptation_log[-1] if self.memory.adaptation_log else "",
            "encouragement": "",
            "matchedKeywords": tech_eval.get("matchedKeywords", []),
            "weaknesses": tech_eval.get("weaknesses", []),
            "missingConcepts": tech_eval.get("missingConcepts", []),
            "strengths": tech_eval.get("strengths", []),
            "drill_down_topic": tech_eval.get("drill_down_topic", ""),
            "depth_analysis": depth_info,
        }

    def _adapt_difficulty(self, metrics: dict, tech_eval: dict, depth_info: dict):
        tech_signal = metrics["technicalScore"]
        depth_signal = metrics["depthOfKnowledge"]
        comm_signal = metrics["communicationScore"]
        conf_signal = metrics["confidenceScore"]
        depth_val = {"deep": 85, "moderate": 60, "shallow": 35, "minimal": 15}.get(depth_info["depth"], 50)
        concept_signal = min(len(self.memory._last_answer_concepts) * 15, 100) if self.memory._last_answer_concepts else 40
        signals = [tech_signal, depth_signal, comm_signal, conf_signal, depth_val, concept_signal]
        overall = sum(signals) / len(signals)
        self.streak_scores.append(overall)

        struggling = overall < 40
        excelling = overall > 70

        if struggling:
            self.consecutive_struggles += 1
            self.consecutive_successes = 0
        elif excelling:
            self.consecutive_successes += 1
            self.consecutive_struggles = 0
        else:
            self.consecutive_struggles = 0
            self.consecutive_successes = 0

        old = self.current_difficulty
        adaptation = f"Maintaining {self.current_difficulty} (avg={overall:.0f})"

        if metrics["confidenceScore"] < 35 and self.current_difficulty != "easy":
            idx = DIFFICULTY_LEVELS.index(self.current_difficulty)
            self.current_difficulty = DIFFICULTY_LEVELS[max(0, idx - 1)]
            self.consecutive_struggles = 0
            adaptation = f"Low confidence ({metrics['confidenceScore']}%). {old} -> {self.current_difficulty}"
            self.encouragement_given += 1
        elif self.consecutive_struggles >= 2 and self.current_difficulty != "easy":
            idx = DIFFICULTY_LEVELS.index(self.current_difficulty)
            self.current_difficulty = DIFFICULTY_LEVELS[max(0, idx - 1)]
            self.consecutive_struggles = 0
            adaptation = f"Struggling. {old} -> {self.current_difficulty}"
            self.encouragement_given += 1
        elif self.consecutive_successes >= 2 and self.current_difficulty != "hard":
            idx = DIFFICULTY_LEVELS.index(self.current_difficulty)
            self.current_difficulty = DIFFICULTY_LEVELS[min(len(DIFFICULTY_LEVELS) - 1, idx + 1)]
            self.consecutive_successes = 0
            adaptation = f"Excelling. {old} -> {self.current_difficulty}"
            self.encouragement_given += 1

        self.memory.adaptation_log.append(adaptation)

    def end_session(self) -> dict:
        scores = self.memory.scores
        if not scores:
            return {"metrics": self._default_metrics(), "adaptation_log": self.memory.adaptation_log}
        avg = {
            "technicalScore": int(sum(s["technicalScore"] for s in scores) / len(scores)),
            "communicationScore": int(sum(s["communicationScore"] for s in scores) / len(scores)),
            "confidenceScore": int(sum(s["confidenceScore"] for s in scores) / len(scores)),
            "engagementScore": int(sum(s["engagementScore"] for s in scores) / len(scores)),
            "stressLevel": int(sum(s["stressLevel"] for s in scores) / len(scores)),
            "depthOfKnowledge": int(sum(s["depthOfKnowledge"] for s in scores) / len(scores)),
        }
        return {"metrics": avg, "adaptation_log": self.memory.adaptation_log}

    def get_feedback(self) -> dict:
        sd = self.end_session()
        return generate_feedback(
            metrics=sd["metrics"],
            questions=self.memory.questions_asked,
            answers=self.memory.answers_given,
            adaptation_log=self.memory.adaptation_log,
        )

    @staticmethod
    def _default_metrics() -> dict:
        return {"technicalScore": 0, "communicationScore": 0, "confidenceScore": 0,
                "engagementScore": 0, "stressLevel": 0, "depthOfKnowledge": 0}
