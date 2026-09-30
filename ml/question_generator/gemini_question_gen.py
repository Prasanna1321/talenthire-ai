"""
ml/question_generator/gemini_question_gen.py
------------------------------------------------
AI Question Generator Module.
Belongs in: ml/question_generator/gemini_question_gen.py

Uses Google's Gemini API (generative AI) to dynamically generate
role-based and skill-based interview questions from a job description
and/or a candidate's extracted resume skills, as required by the report's
"Interview Question Generation Module".

Returns structured JSON so the backend can insert rows directly into the
`interview_questions` table (question_text, question_type, difficulty,
ideal_answer).
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import List, Optional

import google.generativeai as genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")


@dataclass
class GeneratedQuestion:
    question_text: str
    question_type: str   # technical | behavioral | situational | coding
    difficulty: str      # easy | medium | hard
    ideal_answer: str


PROMPT_TEMPLATE = """You are an expert technical interviewer. Generate {num_questions} interview
questions for the role of "{job_role}".

Candidate's known skills: {skills}
Job description context: {job_description}

Requirements:
- Mix of question_type values: technical, behavioral, situational (unless role is clearly coding-heavy, include 1 coding question).
- Distribute difficulty across easy, medium, hard as requested: {difficulty}.
- For each question, also provide a concise "ideal_answer" (2-4 sentences) that a
  strong candidate would give. This will be used as a reference answer for
  semantic-similarity scoring, so it must be substantive and specific.

Return ONLY valid JSON (no markdown fences, no commentary) in this exact schema:
[
  {{
    "question_text": "...",
    "question_type": "technical",
    "difficulty": "medium",
    "ideal_answer": "..."
  }}
]
"""


class GeminiQuestionGenerator:
    def __init__(self, api_key: str = GEMINI_API_KEY, model_name: str = GEMINI_MODEL):
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set. Add it to backend/.env")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    def generate(
        self,
        job_role: str,
        skills: Optional[List[str]] = None,
        job_description: str = "",
        num_questions: int = 5,
        difficulty: str = "mixed",
    ) -> List[GeneratedQuestion]:
        prompt = PROMPT_TEMPLATE.format(
            num_questions=num_questions,
            job_role=job_role,
            skills=", ".join(skills) if skills else "not specified",
            job_description=job_description or "not specified",
            difficulty=difficulty,
        )

        response = self.model.generate_content(prompt)
        raw_text = response.text.strip()

        # Gemini sometimes wraps JSON in ```json ... ``` fences despite instructions
        raw_text = re.sub(r"^```(json)?|```$", "", raw_text, flags=re.MULTILINE).strip()

        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Gemini returned malformed JSON: {exc}\nRaw: {raw_text[:500]}")

        return [
            GeneratedQuestion(
                question_text=item["question_text"],
                question_type=item.get("question_type", "technical"),
                difficulty=item.get("difficulty", "medium"),
                ideal_answer=item.get("ideal_answer", ""),
            )
            for item in parsed
        ]


_generator_instance: GeminiQuestionGenerator | None = None


def get_question_generator() -> GeminiQuestionGenerator:
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = GeminiQuestionGenerator()
    return _generator_instance
