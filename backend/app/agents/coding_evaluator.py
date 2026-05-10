import json
import os
import random
import re
from pathlib import Path
from typing import Optional

from ..services.groq_client import groq_json

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PROBLEMS_FILE = DATA_DIR / "coding_problems.json"


def load_all_problems() -> list[dict]:
    if not PROBLEMS_FILE.exists():
        return []
    with open(PROBLEMS_FILE) as f:
        return json.load(f)


def get_problems_by_filters(
    difficulty: Optional[str] = None,
    category: Optional[str] = None,
    avoid_ids: Optional[list[str]] = None,
) -> list[dict]:
    problems = load_all_problems()
    if difficulty:
        problems = [p for p in problems if p["difficulty"] == difficulty]
    if category:
        problems = [p for p in problems if p["category"] == category]
    if avoid_ids:
        problems = [p for p in problems if p["id"] not in avoid_ids]
    return problems


def get_challenge(difficulty: str, avoid_ids: list[str], category: Optional[str] = None) -> dict:
    candidates = get_problems_by_filters(difficulty, category, avoid_ids)
    if not candidates:
        candidates = get_problems_by_filters(None, category, avoid_ids)
        if not candidates:
            candidates = load_all_problems()
    return random.choice(candidates) if candidates else _fallback_challenge(difficulty)


def get_all_categories() -> list[str]:
    problems = load_all_problems()
    cats = sorted(set(p["category"] for p in problems if "category" in p))
    return cats


async def generate_coding_challenge_async(difficulty: str) -> Optional[dict]:
    prompt = (
        f"Generate a {difficulty} coding challenge for a technical interview. "
        f"Return JSON with: title, description, example, starter_code (Python), "
        f"constraints (list), test_cases (list of {{input, expected}}), "
        f"hidden_test_cases (list of {{input, expected}}), "
        f"time_complexity_expected, space_complexity_expected, hints (list)."
    )
    result = await groq_json("coding_challenge_generator", prompt, temperature=0.7, max_tokens=2500)
    if result and "title" in result and "starter_code" in result:
        return result
    return None


async def select_problem_ai(
    difficulty: str,
    avoid_ids: list[str],
    performance_history: Optional[dict] = None,
    category: Optional[str] = None,
) -> Optional[dict]:
    candidates = get_problems_by_filters(difficulty, category, avoid_ids)
    if not candidates:
        candidates = get_problems_by_filters(None, category, avoid_ids)
    if not candidates:
        candidates = load_all_problems()

    if not candidates:
        return _fallback_challenge(difficulty)

    if performance_history and len(candidates) > 3:
        prompt = (
            f"Candidate performance history: {json.dumps(performance_history)}. "
            f"Available problems: {json.dumps([{'id': p['id'], 'title': p['title'], 'category': p['category'], 'difficulty': p['difficulty']} for p in candidates])}. "
            f"Select the best next problem. Return JSON with just the selected 'id'."
        )
        result = await groq_json("coding_challenge_selector", prompt, temperature=0.3, max_tokens=200)
        if result and "id" in result:
            for p in candidates:
                if p["id"] == result["id"]:
                    return p

    return random.choice(candidates)


async def evaluate_coding_solution_async(problem: str, solution: str) -> Optional[dict]:
    if not solution.strip():
        return None
    prompt = (
        f"Evaluate this coding solution. Be strict but fair.\n\n"
        f"Problem: {problem}\n\n"
        f"Candidate Solution:\n{solution}\n\n"
        f"Return JSON with correctnessScore (0-99), timeComplexity, spaceComplexity, "
        f"feedback, suggestions, and doesCompile (bool)."
    )
    return await groq_json("coding_evaluator", prompt, temperature=0.2, max_tokens=1000)


async def generate_follow_up_async(
    problem: dict, code: str, question_type: str
) -> Optional[dict]:
    prompt = (
        f"Coding problem: {problem.get('title', '')} - {problem.get('description', '')}\n\n"
        f"Candidate solution:\n{code}\n\n"
        f"Generate a follow-up question about {question_type.replace('_', ' ')}. "
        f"Return JSON with 'question' (the follow-up question), "
        f"'expectedAnswer' (what a good candidate should say), "
        f"and 'hint' (a small nudge if they struggle)."
    )
    return await groq_json("coding_followup", prompt, temperature=0.5, max_tokens=500)


def _fallback_challenge(difficulty: str) -> dict:
    return {
        "id": "fallback",
        "title": "Reverse a String",
        "category": "strings",
        "difficulty": difficulty,
        "description": "Write a function that reverses a string in-place.",
        "example": "Input: ['h','e','l','l','o']\nOutput: ['o','l','l','e','h']",
        "starter_code": "def reverse_string(s):\n    # Write your code here (modify in-place)\n    pass\n\n# Test\ns = ['h','e','l','l','o']\nreverse_string(s)\nprint(s)  # Expected: ['o', 'l', 'l', 'e', 'h']",
        "constraints": ["Do not allocate extra space for another array", "Modify in-place with O(1) memory"],
        "time_complexity_expected": "O(n)",
        "space_complexity_expected": "O(1)",
        "test_cases": [
            {"input": "['h','e','l','l','o']", "expected": "['o','l','l','e','h']"},
            {"input": "['H','a','n','n','a','h']", "expected": "['h','a','n','n','a','H']"},
        ],
        "hidden_test_cases": [
            {"input": "['a','b','c','d']", "expected": "['d','c','b','a']"},
            {"input": "['x']", "expected": "['x']"},
        ],
        "hints": ["Use two-pointer approach: swap left and right elements while left < right"],
    }


def evaluate_coding_solution(problem: str, solution: str) -> dict:
    if not solution.strip():
        return {
            "correctnessScore": 0,
            "timeComplexity": "N/A",
            "spaceComplexity": "N/A",
            "feedback": "No solution provided.",
            "suggestions": ["Write your code solution to receive feedback."],
            "doesCompile": False,
            "hiddenTestsPassed": 0,
            "hiddenTestsTotal": 0,
            "followUpQuestions": [],
        }

    lines = solution.strip().split("\n")
    code_lines = [l for l in lines if l.strip() and not l.strip().startswith("#")]
    has_def = any(l.strip().startswith("def ") or l.strip().startswith("class ") for l in lines)
    has_return = "return" in solution
    has_loop = any(kw in solution for kw in ["for ", "while "])
    has_conditional = "if " in solution

    score = 0
    if has_def:
        score += 20
    if has_return:
        score += 15
    if len(code_lines) >= 5:
        score += 15
    elif len(code_lines) >= 3:
        score += 10
    if has_loop:
        score += 15
    if has_conditional:
        score += 10
    has_docstring = '"""' in solution or "'''" in solution
    if has_docstring:
        score += 5
    if len(code_lines) >= 10:
        score += 10
    elif len(code_lines) >= 7:
        score += 5
    has_edge_checks = any(kw in solution for kw in ["if not", "if len", "isEmpty", "is None"])
    if has_edge_checks:
        score += 10

    score = min(score, 99)

    if "for" in solution and "while" in solution:
        time_c = "O(n²) or worse"
    elif "for" in solution or "while" in solution:
        time_c = "O(n)"
    else:
        time_c = "O(1)"

    space_c = "O(1)"
    if "list(" in solution or "[]" in solution or "dict(" in solution or "{}" in solution:
        space_c = "O(n)"

    suggestions = []
    if score < 40:
        suggestions.append("Add function signature with proper input parameters")
        suggestions.append("Implement the core logic before testing edge cases")
    if not has_edge_checks:
        suggestions.append("Handle edge cases (empty input, None values)")
    if not has_docstring:
        suggestions.append("Add docstrings for better code documentation")
    if score >= 70:
        suggestions.append("Consider optimizing for time/space complexity")

    feedback = (
        "Good solution structure! " if has_def and has_return else
        "Solution needs more structure. " if not has_def else
        "Decent attempt, but missing key elements. "
    )
    if score >= 70:
        feedback += "Strong implementation with solid logic."
    elif score >= 50:
        feedback += "On the right track. Review the suggestions below."
    else:
        feedback += "Review fundamentals and try a structured approach."

    return {
        "correctnessScore": score,
        "timeComplexity": time_c,
        "spaceComplexity": space_c,
        "feedback": feedback,
        "suggestions": suggestions[:4],
        "doesCompile": has_def and has_return,
        "hiddenTestsPassed": 0,
        "hiddenTestsTotal": 0,
        "followUpQuestions": [],
    }