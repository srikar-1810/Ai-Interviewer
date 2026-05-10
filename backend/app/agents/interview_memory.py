"""
Conversation Memory System for intelligent interviews.
Tracks topics, deduplicates questions, manages state transitions.
Supports full serialization for session persistence.
"""

from typing import Any
from collections import Counter
import re


# ── Topic Taxonomy ──────────────────────────────────────────────

TOPIC_TAXONOMY = {
    "programming_fundamentals": {
        "keywords": ["variable", "loop", "function", "class", "object", "inheritance", "polymorphism",
                     "encapsulation", "abstraction", "recursion", "iteration", "data type", "compiler",
                     "interpreter", "memory", "stack", "heap", "thread", "process", "async", "callback",
                     "promise", "event loop", "garbage collection", "scope", "closure"],
        "depth_labels": ["definition", "usage", "internals", "optimization", "design"],
        "subtopics": ["variables", "control_flow", "functions", "oop", "memory_management", "concurrency"],
    },
    "data_structures": {
        "keywords": ["array", "list", "linked list", "stack", "queue", "tree", "graph", "hash",
                     "map", "set", "heap", "trie", "priority queue", "deque", "binary tree",
                     "binary search tree", "balanced tree", "hashmap", "hash table"],
        "depth_labels": ["definition", "implementation", "complexity", "application", "tradeoff"],
        "subtopics": ["arrays", "linked_lists", "stacks_queues", "trees", "graphs", "hashtables", "heaps"],
    },
    "algorithms": {
        "keywords": ["sort", "search", "binary search", "dynamic programming", "greedy", "divide and conquer",
                     "backtracking", "bfs", "dfs", "dijkstra", "shortest path", "minimum spanning tree",
                     "topological sort", "sliding window", "two pointer", "memoization", "recursion",
                     "time complexity", "space complexity", "big o"],
        "depth_labels": ["concept", "implementation", "complexity", "optimization", "application"],
        "subtopics": ["sorting", "searching", "dp", "graph_algorithms", "complexity_analysis"],
    },
    "databases": {
        "keywords": ["sql", "nosql", "index", "query", "transaction", "acid", "normalization",
                     "denormalization", "sharding", "replication", "partition", "orm", "join",
                     "subquery", "view", "trigger", "stored procedure", "migration", "schema",
                     "cap theorem", "eventual consistency", "strong consistency", "b tree",
                     "query optimization", "connection pool", "read replica"],
        "depth_labels": ["concept", "syntax", "internals", "optimization", "design"],
        "subtopics": ["sql", "nosql", "indexing", "transactions", "normalization", "sharding", "cap_theorem"],
    },
    "system_design": {
        "keywords": ["microservices", "monolith", "api gateway", "load balancer", "caching", "cdn",
                     "message queue", "pub sub", "event driven", "distributed", "scalability",
                     "availability", "latency", "throughput", "rate limiting", "circuit breaker",
                     "service mesh", "container", "orchestration", "rpc", "rest", "graphql",
                     "webhook", "batch processing", "stream processing", "consistency",
                     "partitioning", "leader election", "paxos", "raft"],
        "depth_labels": ["concept", "architecture", "tradeoff", "scalability", "implementation"],
        "subtopics": ["distributed_systems", "microservices", "caching", "load_balancing", "databases", "apis"],
    },
    "frontend": {
        "keywords": ["react", "vue", "angular", "component", "state management", "props", "hook",
                     "virtual dom", "rendering", "css", "responsive", "accessibility", "bundle",
                     "lazy loading", "ssr", "csr", "webpack", "vite", "typescript", "dom",
                     "event loop", "closure", "promise", "async await", "redux", "context"],
        "depth_labels": ["concept", "implementation", "performance", "architecture", "ecosystem"],
        "subtopics": ["frameworks", "state_management", "rendering", "performance", "typescript"],
    },
    "backend": {
        "keywords": ["api", "rest", "graphql", "authentication", "authorization", "middleware",
                     "webhook", "rate limit", "error handling", "logging", "monitoring", "worker",
                     "cron", "web socket", "session", "jwt", "oauth", "ssl", "cors", "nosql",
                     "redis", "rabbitmq", "kafka", "docker", "kubernetes", "serverless"],
        "depth_labels": ["concept", "implementation", "security", "scalability", "best practice"],
        "subtopics": ["apis", "auth", "middleware", "message_queues", "containers", "serverless"],
    },
    "devops": {
        "keywords": ["ci/cd", "docker", "kubernetes", "terraform", "ansible", "jenkins", "github actions",
                     "monitoring", "prometheus", "grafana", "elk", "cloud", "aws", "gcp",
                     "azure", "infrastructure as code", "blue green deployment", "canary",
                     "rollback", "health check", "sla", "slo", "incident response"],
        "depth_labels": ["concept", "tool", "pipeline", "best practice", "incident"],
        "subtopics": ["ci_cd", "containers", "cloud", "monitoring", "iac"],
    },
    "behavioral": {
        "keywords": ["leadership", "ownership", "collaboration", "mentor", "conflict", "deadline",
                     "stakeholder", "initiative", "impact", "team", "challenge", "solution",
                     "result", "learn", "improve", "communication", "feedback", "agile",
                     "sprint", "retrospective", "cross functional", "growth"],
        "depth_labels": ["experience", "approach", "outcome", "learning", "growth"],
        "subtopics": ["leadership", "teamwork", "conflict", "growth", "communication"],
    },
}


# ── Similarity Helpers ──────────────────────────────────────────

def _tokenize(text: str) -> set[str]:
    return set(re.findall(r'\b[a-z]{3,}\b', text.lower()))


def _bigrams(text: str) -> set[str]:
    tokens = sorted(_tokenize(text))
    return set(" ".join(tokens[i:i+2]) for i in range(len(tokens) - 1))


def _jaccard_similarity(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _longest_common_substring_ratio(a: str, b: str) -> float:
    a, b = a.lower(), b.lower()
    m, n = len(a), len(b)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    longest = 0
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
                longest = max(longest, dp[i][j])
    return longest / max(len(a), len(b), 1)


def _extract_key_concepts(text: str) -> set[str]:
    """Extract important technical/conceptual phrases from text."""
    text_lower = text.lower()
    concepts = set()
    for topic, info in TOPIC_TAXONOMY.items():
        for kw in info["keywords"]:
            if kw.lower() in text_lower:
                concepts.add(kw.lower())
    return concepts


def _ngram_overlap(a: str, b: str, n: int = 3) -> float:
    """Character n-gram overlap for short-text similarity."""
    def ngrams(s):
        s = s.lower()
        return set(s[i:i+n] for i in range(len(s) - n + 1))
    ag = ngrams(a)
    bg = ngrams(b)
    if not ag or not bg:
        return 0.0
    return len(ag & bg) / len(ag | bg)


# ── Classifier ──────────────────────────────────────────────────

def classify_question_topic(question_text: str) -> tuple[str, float, int]:
    tokens = _tokenize(question_text)
    scores: list[tuple[str, float, int]] = []
    for topic, info in TOPIC_TAXONOMY.items():
        kw_set = set(k.lower() for k in info["keywords"])
        overlap = len(tokens & kw_set)
        if overlap > 0:
            jaccard = _jaccard_similarity(tokens, kw_set)
            scores.append((topic, jaccard, overlap))
    scores.sort(key=lambda x: (-x[1], -x[2]))
    return scores[0] if scores else ("general", 0.0, 0)


def classify_subtopic(text: str) -> str | None:
    """Classify text into a subtopic within a topic taxonomy."""
    text_lower = text.lower()
    for topic, info in TOPIC_TAXONOMY.items():
        subtopics = info.get("subtopics", [])
        for st in subtopics:
            st_keywords = st.replace("_", " ").split()
            if all(kw in text_lower for kw in st_keywords):
                return st
    return None


# ── Conversation Memory ─────────────────────────────────────────

class ConversationMemory:
    def __init__(self):
        # Public tracking
        self.questions_asked: list[dict] = []
        self.answers_given: list[str] = []
        self.conversation_history: list[dict] = []
        self.scores: list[dict] = []
        self.adaptation_log: list[str] = []
        self.encouragements: list[str] = []

        # Topic tracking
        self._topic_coverage: dict[str, dict[str, Any]] = {}
        self._concepts_covered: set[str] = set()
        self._concept_phrases: list[str] = []

        # Answer concept extraction
        self._answer_concepts: list[set[str]] = []
        self._answer_ngrams: list[set[str]] = []

        # Follow-up chains
        self._follow_up_chain: list[str] = []
        self._current_probing_topic: str | None = None
        self._probe_depth_count: int = 0
        self._max_probe_depth: int = 3

        # Weakness & strength tracking
        self._weakness_signals: list[dict] = []
        self._strength_accumulator: dict[str, int] = {}

        # Conversation flow
        self._last_answer_quality: str = "unseen"
        self._last_answer_concepts: set[str] = set()
        self._topic_transition_count: int = 0

    # ── Serialization ──

    def to_dict(self) -> dict:
        # Deep-clean _topic_coverage: convert sets to lists for JSON
        clean_topic_coverage = {}
        for topic, info in self._topic_coverage.items():
            clean_info = dict(info)
            for key in ("concepts_asked", "subtopics_covered"):
                if isinstance(clean_info.get(key), set):
                    clean_info[key] = list(clean_info[key])
            clean_topic_coverage[topic] = clean_info

        return {
            "questions_asked": self.questions_asked,
            "answers_given": self.answers_given,
            "conversation_history": self.conversation_history,
            "scores": self.scores,
            "adaptation_log": self.adaptation_log,
            "encouragements": self.encouragements,
            "_topic_coverage": clean_topic_coverage,
            "_concepts_covered": list(self._concepts_covered),
            "_concept_phrases": self._concept_phrases,
            "_answer_concepts": [list(s) for s in self._answer_concepts],
            "_follow_up_chain": self._follow_up_chain,
            "_current_probing_topic": self._current_probing_topic,
            "_probe_depth_count": self._probe_depth_count,
            "_weakness_signals": self._weakness_signals,
            "_strength_accumulator": dict(self._strength_accumulator),
            "_last_answer_quality": self._last_answer_quality,
            "_last_answer_concepts": list(self._last_answer_concepts),
            "_topic_transition_count": self._topic_transition_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ConversationMemory":
        m = cls()
        m.questions_asked = data.get("questions_asked", [])
        m.answers_given = data.get("answers_given", [])
        m.conversation_history = data.get("conversation_history", [])
        m.scores = data.get("scores", [])
        m.adaptation_log = data.get("adaptation_log", [])
        m.encouragements = data.get("encouragements", [])

        # Restore topic coverage — convert lists back to sets
        raw_tc = data.get("_topic_coverage", {})
        m._topic_coverage = {}
        for topic, info in raw_tc.items():
            restored = dict(info)
            for key in ("concepts_asked", "subtopics_covered"):
                if isinstance(restored.get(key), list):
                    restored[key] = set(restored[key])
            m._topic_coverage[topic] = restored

        m._concepts_covered = set(data.get("_concepts_covered", []))
        m._concept_phrases = data.get("_concept_phrases", [])
        m._answer_concepts = [set(s) for s in data.get("_answer_concepts", [])]
        m._follow_up_chain = data.get("_follow_up_chain", [])
        m._current_probing_topic = data.get("_current_probing_topic")
        m._probe_depth_count = data.get("_probe_depth_count", 0)
        m._weakness_signals = data.get("_weakness_signals", [])
        m._strength_accumulator = dict(data.get("_strength_accumulator", {}))
        m._last_answer_quality = data.get("_last_answer_quality", "unseen")
        m._last_answer_concepts = set(data.get("_last_answer_concepts", []))
        m._topic_transition_count = data.get("_topic_transition_count", 0)
        return m

    # ── Topic Tracking ──

    def track_question(self, question: dict, answer: str = ""):
        self.questions_asked.append(question)
        if answer:
            self.answers_given.append(answer)
            self.conversation_history.append({"role": "user", "content": answer})

        q_text = question.get("text", "")
        topic, confidence, _ = classify_question_topic(q_text)
        if topic == "general":
            topic = question.get("type", "technical")

        if topic not in self._topic_coverage:
            self._topic_coverage[topic] = {
                "count": 0, "max_depth": 0, "questions": [], "answers": [],
                "concepts_asked": set(), "subtopics_covered": set(),
            }
        self._topic_coverage[topic]["count"] += 1
        self._topic_coverage[topic]["questions"].append(q_text[:120])

        # Track subtopic coverage within this topic
        subtopic = classify_subtopic(q_text)
        if subtopic:
            self._topic_coverage[topic]["subtopics_covered"].add(subtopic)

        # Track concepts asked about in this topic
        q_concepts = _extract_key_concepts(q_text)
        self._topic_coverage[topic]["concepts_asked"].update(q_concepts)

        if answer:
            self._topic_coverage[topic]["answers"].append(answer[:200])

        # Probe depth tracking
        if self._current_probing_topic == topic:
            self._probe_depth_count += 1
        else:
            self._current_probing_topic = topic
            self._probe_depth_count = 1
            self._topic_transition_count += 1
        self._topic_coverage[topic]["max_depth"] = max(
            self._topic_coverage[topic]["max_depth"], self._probe_depth_count
        )

        concepts = _tokenize(q_text)
        self._concepts_covered |= concepts
        self._concept_phrases.append(q_text)

    def track_answer(self, answer: str):
        """Track extracted concepts and quality signals from an answer."""
        concepts = _extract_key_concepts(answer)
        self._answer_concepts.append(concepts)
        self._last_answer_concepts = concepts
        self._answer_ngrams.append(_bigrams(answer))

    def track_answer_quality(self, depth_label: str):
        self._last_answer_quality = depth_label

    def track_answer_analysis(self, analysis: dict):
        score = analysis.get("correctnessScore", 50)
        depth = analysis.get("depthOfKnowledge", 50)
        weaknesses = analysis.get("weaknesses", [])
        missing = analysis.get("missingConcepts", [])
        strengths = analysis.get("strengths", [])

        for w in weaknesses:
            self._weakness_signals.append({
                "weakness": w,
                "question_idx": len(self.questions_asked) - 1,
            })
        for m in missing:
            self._concepts_covered.discard(m.lower().strip())

        for s in strengths:
            if isinstance(s, str):
                key = s.lower().strip()
                self._strength_accumulator[key] = self._strength_accumulator.get(key, 0) + 1

    # ── Deduplication ──

    def is_duplicate(self, new_question_text: str, threshold: float = 0.40) -> tuple[bool, str, float]:
        """Multi-strategy dedup: token Jaccard, LCS, bigram overlap, concept overlap."""
        new_tokens = _tokenize(new_question_text)
        new_concepts = _extract_key_concepts(new_question_text)

        for existing in self.questions_asked:
            existing_text = existing.get("text", "")

            # Token Jaccard
            j_sim = _jaccard_similarity(new_tokens, _tokenize(existing_text))

            # LCS ratio
            lcs = _longest_common_substring_ratio(new_question_text, existing_text)

            # Concept overlap — if both have concepts and they overlap significantly
            existing_concepts = _extract_key_concepts(existing_text)
            concept_overlap = _jaccard_similarity(new_concepts, existing_concepts) if new_concepts or existing_concepts else 0.0

            # Character n-gram overlap
            ngram_sim = _ngram_overlap(new_question_text, existing_text)

            combined = max(j_sim, lcs, ngram_sim, concept_overlap * 0.8)
            if combined >= threshold:
                return (True, existing_text[:80], round(combined, 2))

        # Check against concept phrases used
        for phrase in self._concept_phrases:
            lcs = _longest_common_substring_ratio(new_question_text, phrase)
            if lcs >= threshold:
                return (True, phrase[:80], round(lcs, 2))

        # Check against answer concepts (detect if we'd be asking about something just discussed)
        for a_concepts in self._answer_concepts:
            concept_overlap = _jaccard_similarity(new_concepts, a_concepts) if new_concepts or a_concepts else 0.0
            if concept_overlap > 0.55:
                return (True, f"concept overlap {concept_overlap:.2f}", round(concept_overlap, 2))

        return (False, "", 0.0)

    def is_topic_exhausted(self, topic: str) -> bool:
        """Check if a topic has been sufficiently covered."""
        info = self._topic_coverage.get(topic)
        if not info:
            return False
        return info["count"] >= 5 or info["max_depth"] >= 4

    # ── Topic Analysis ──

    def get_covered_topics_summary(self) -> str:
        if not self._topic_coverage:
            return "No topics covered yet."
        parts = []
        for topic, info in sorted(self._topic_coverage.items(), key=lambda x: -x[1]["count"]):
            subtopics = info.get("subtopics_covered", set())
            sub_str = f" [{', '.join(sorted(subtopics)[:3])}]" if subtopics else ""
            parts.append(f"- {topic}: {info['count']}q depth={info['max_depth']}{sub_str}")
        return "\n".join(parts[:8])

    def get_remaining_subtopics(self, topic: str) -> list[str]:
        """Get subtopics within a topic that haven't been covered."""
        info = TOPIC_TAXONOMY.get(topic, {})
        all_subtopics = set(info.get("subtopics", []))
        covered = self._topic_coverage.get(topic, {}).get("subtopics_covered", set())
        return list(all_subtopics - covered)

    def get_uncovered_topics(self) -> list[str]:
        covered = set(self._topic_coverage.keys())
        return [t for t in TOPIC_TAXONOMY if t not in covered and t != "general"]

    def get_weakness_summary(self) -> str:
        if not self._weakness_signals:
            return "No significant weaknesses detected."
        return "; ".join(set(w["weakness"] for w in self._weakness_signals))

    def get_strength_summary(self) -> str:
        if not self._strength_accumulator:
            return "No notable strengths detected yet."
        sorted_s = sorted(self._strength_accumulator.items(), key=lambda x: -x[1])[:5]
        return "; ".join(f"{k} (x{v})" for k, v in sorted_s)

    def get_performance_trend(self) -> str:
        if len(self.scores) < 2:
            return "Not enough data for trend."
        recent = self.scores[-3:]
        avg = sum(s.get("technicalScore", 50) for s in recent) / len(recent)
        if avg >= 70:
            return "strong"
        elif avg >= 45:
            return "moderate"
        return "struggling"

    def get_drill_recommendation(self) -> str | None:
        """Suggest a topic/concept that needs deeper probing."""
        # Find the most recent weakness that hasn't been followed up
        if self._weakness_signals:
            latest = self._weakness_signals[-1]["weakness"]
            return latest
        # Check if any topic has only surface-level coverage
        for topic, info in sorted(self._topic_coverage.items(), key=lambda x: x[1]["count"]):
            if info["max_depth"] <= 1 and info["count"] >= 1:
                return topic
        return None

    def get_follow_up_context(self) -> dict:
        """Return context about what happened in the last exchange."""
        return {
            "last_answer_quality": self._last_answer_quality,
            "last_answer_concepts": list(self._last_answer_concepts)[:8],
            "current_probe_topic": self._current_probing_topic,
            "probe_depth": self._probe_depth_count,
            "topic_transition_count": self._topic_transition_count,
            "last_question": self.questions_asked[-1]["text"] if self.questions_asked else "",
            "last_answer": self.answers_given[-1] if self.answers_given else "",
        }


# ── Interview State Machine ─────────────────────────────────────

INTERVIEW_STAGES = [
    "introduction",
    "resume_discussion",
    "technical_fundamentals",
    "intermediate_concepts",
    "advanced_technical",
    "projects",
    "algorithms_problem_solving",
    "behavioral",
    "wrap_up",
]

STAGE_WEIGHTS = {
    "introduction": 0.5,
    "resume_discussion": 1.0,
    "technical_fundamentals": 1.5,
    "intermediate_concepts": 2.0,
    "advanced_technical": 2.0,
    "projects": 1.5,
    "algorithms_problem_solving": 1.5,
    "behavioral": 1.0,
    "wrap_up": 0.5,
}


class InterviewStateMachine:
    def __init__(self):
        self.stage_index: int = 0
        self.stage_question_counts: dict[str, int] = {s: 0 for s in INTERVIEW_STAGES}
        self.force_transition: bool = False
        self.skipped_stages: set[str] = set()
        self._total_stage_transitions: int = 0

    @property
    def current_stage(self) -> str:
        return INTERVIEW_STAGES[self.stage_index]

    def get_next_stage(self) -> str | None:
        for i in range(self.stage_index + 1, len(INTERVIEW_STAGES)):
            if INTERVIEW_STAGES[i] not in self.skipped_stages:
                return INTERVIEW_STAGES[i]
        return None

    def advance(self):
        if self.stage_index < len(INTERVIEW_STAGES) - 1:
            self.stage_index += 1
            self.force_transition = False
            self._total_stage_transitions += 1

    def should_transition(self, memory: ConversationMemory, metrics: dict) -> bool:
        stage = self.current_stage
        q_count = self.stage_question_counts[stage]

        # Stages have minimum questions
        min_q = max(1, int(STAGE_WEIGHTS.get(stage, 1.0) * 2))
        if q_count < min_q:
            return False

        # Don't advance if underperforming in technical stages
        if stage in ("technical_fundamentals", "intermediate_concepts", "advanced_technical"):
            perf = memory.get_performance_trend()
            if perf == "struggling" and q_count < min_q + 2:
                return False

        # If all uncovered topics in current stage are covered, advance
        if stage == "technical_fundamentals":
            uncovered = memory.get_uncovered_topics()
            fundamentals = ["programming_fundamentals", "data_structures", "algorithms"]
            if all(t not in uncovered for t in fundamentals) and q_count >= min_q:
                return True

        # Advance after sufficient questions
        if q_count >= min_q + 2:
            return True

        # Don't let intro/resume take too long
        total_q = len(memory.questions_asked)
        if total_q >= 3 and stage in ("introduction", "resume_discussion"):
            return True

        return self.force_transition

    def get_context_for_prompt(self, memory: ConversationMemory) -> dict:
        stage = self.current_stage
        uncovered = memory.get_uncovered_topics()
        follow_up = memory.get_follow_up_context()
        remaining_subs = memory.get_remaining_subtopics(stage)

        return {
            "stage": stage,
            "stage_description": self._describe_stage(stage),
            "questions_in_stage": self.stage_question_counts[stage],
            "uncovered_topics": uncovered,
            "remaining_subtopics": remaining_subs,
            "next_stage": self.get_next_stage(),
            "performance_trend": memory.get_performance_trend(),
            "weaknesses": memory.get_weakness_summary(),
            "strengths": memory.get_strength_summary(),
            "topic_coverage": memory.get_covered_topics_summary(),
            "drill_recommendation": memory.get_drill_recommendation(),
            "follow_up_context": follow_up,
            "total_stage_transitions": self._total_stage_transitions,
        }

    @staticmethod
    def _describe_stage(stage: str) -> str:
        descriptions = {
            "introduction": "Warm-up: Tell me about yourself, background, motivations. 1-2 questions.",
            "resume_discussion": "Discuss resume details: past roles, responsibilities, technologies used, team size, impact.",
            "technical_fundamentals": "Core technical concepts: data structures, algorithms, language fundamentals, CS basics. Verify foundations.",
            "intermediate_concepts": "Intermediate topics: databases, APIs, system components, design patterns, testing, performance.",
            "advanced_technical": "Deep technical topics: system design, distributed systems, scalability, optimization, architecture trade-offs, real-world engineering challenges.",
            "projects": "Deep-dive into specific projects: architecture decisions, challenges, technical implementations, outcomes, trade-offs made.",
            "algorithms_problem_solving": "Algorithmic problem-solving: coding challenges, time/space complexity, optimal vs practical solutions.",
            "behavioral": "Soft skills, leadership, teamwork, conflict resolution, career goals, situational questions.",
            "wrap_up": "Final questions for the candidate, next steps, feedback session.",
        }
        return descriptions.get(stage, stage.replace("_", " ").title())

    def to_dict(self) -> dict:
        return {
            "stage_index": self.stage_index,
            "stage_question_counts": self.stage_question_counts,
            "skipped_stages": list(self.skipped_stages),
            "_total_stage_transitions": self._total_stage_transitions,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "InterviewStateMachine":
        sm = cls()
        sm.stage_index = data.get("stage_index", 0)
        sm.stage_question_counts = data.get("stage_question_counts", {s: 0 for s in INTERVIEW_STAGES})
        sm.skipped_stages = set(data.get("skipped_stages", []))
        sm._total_stage_transitions = data.get("_total_stage_transitions", 0)
        return sm


# ── Answer Depth Analysis ───────────────────────────────────────

def analyze_answer_depth(answer: str) -> dict:
    if not answer:
        return {"depth": "none", "word_count": 0, "has_example": False, "has_metrics": False,
                "has_structure": False, "has_tradeoffs": False, "signal_count": 0}

    words = answer.split()
    wc = len(words)

    has_example = any(phrase in answer.lower() for phrase in [
        "for example", "for instance", "such as", "specifically", "in practice",
        "in my experience", "i built", "i implemented", "i designed", "i led",
    ])

    has_metrics = any(char in answer for char in ["%", "x "]) or any(
        word.isdigit() and int(word) > 10 for word in words
    )

    has_structure = any(phrase in answer.lower() for phrase in [
        "first", "second", "third", "finally", "in conclusion",
        "firstly", "secondly", "lastly", "to begin",
    ])

    has_tradeoffs = any(phrase in answer.lower() for phrase in [
        "tradeoff", "trade-off", "pros and cons", "advantage", "disadvantage",
        "benefit", "drawback", "consider", "alternative", "instead",
    ])

    has_comparison = any(phrase in answer.lower() for phrase in [
        "compared to", "versus", "vs", "on the other hand", "however",
        "whereas", "while", "although",
    ])

    signal_count = sum([has_example, has_metrics, has_structure, has_tradeoffs, has_comparison])

    if wc >= 80 and signal_count >= 2:
        depth = "deep"
    elif wc >= 40 and signal_count >= 1:
        depth = "moderate"
    elif wc >= 15:
        depth = "shallow"
    else:
        depth = "minimal"

    return {
        "depth": depth,
        "word_count": wc,
        "has_example": has_example,
        "has_metrics": has_metrics,
        "has_structure": has_structure,
        "has_tradeoffs": has_tradeoffs,
        "has_comparison": has_comparison,
        "signal_count": signal_count,
    }
