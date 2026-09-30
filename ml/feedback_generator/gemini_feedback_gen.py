"""
ml/feedback_generator/gemini_feedback_gen.py
------------------------------------------------
AI Feedback Module.
Belongs in: ml/feedback_generator/gemini_feedback_gen.py

Uses Gemini to turn a full interview session's Q&A + numeric scores into
a personalized qualitative feedback report (strengths, areas to improve,
detailed narrative feedback, overall rating out of 10) — the report's
"personalized performance feedback" requirement.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import List, TypedDict

import google.generativeai as genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")


class QAPair(TypedDict):
    question: str
    answer: str
    final_score: float


@dataclass
class GeneratedFeedback:
    strengths: str
    areas_to_improve: str
    detailed_feedback: str
    overall_rating: float


PROMPT_TEMPLATE = """You are an experienced technical interview coach. Below is a candidate's
mock interview transcript with per-answer scores (0-100 scale, weighted from
semantic relevance, fluency, and confidence).

{transcript}

Write personalized, constructive feedback for this candidate. Be specific —
reference the actual questions/answers, not generic advice.

Return ONLY valid JSON (no markdown fences) in this schema:
{{
  "strengths": "2-3 sentences on what the candidate did well",
  "areas_to_improve": "2-3 sentences on concrete improvement areas",
  "detailed_feedback": "A short paragraph (4-6 sentences) with an overall assessment and specific next steps",
  "overall_rating": 7.5
}}
overall_rating must be a number between 0 and 10.
"""


class GeminiFeedbackGenerator:
    def __init__(self, api_key: str = GEMINI_API_KEY, model_name: str = GEMINI_MODEL):
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set. Add it to backend/.env")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    def generate(self, qa_pairs: List[QAPair]) -> GeneratedFeedback:
        transcript_lines = []
        for i, pair in enumerate(qa_pairs, start=1):
            transcript_lines.append(
                f"Q{i}: {pair['question']}\n"
                f"A{i}: {pair['answer']}\n"
                f"Score{i}: {pair['final_score']}/100\n"
            )
        transcript = "\n".join(transcript_lines)
        prompt = PROMPT_TEMPLATE.format(transcript=transcript)

        response = self.model.generate_content(prompt)
        raw_text = response.text.strip()
        raw_text = re.sub(r"^```(json)?|```$", "", raw_text, flags=re.MULTILINE).strip()

        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Gemini returned malformed JSON: {exc}\nRaw: {raw_text[:500]}")

        return GeneratedFeedback(
            strengths=parsed.get("strengths", ""),
            areas_to_improve=parsed.get("areas_to_improve", ""),
            detailed_feedback=parsed.get("detailed_feedback", ""),
            overall_rating=float(parsed.get("overall_rating", 0)),
        )


_feedback_generator_instance: GeminiFeedbackGenerator | None = None


def get_feedback_generator() -> GeminiFeedbackGenerator:
    global _feedback_generator_instance
    if _feedback_generator_instance is None:
        _feedback_generator_instance = GeminiFeedbackGenerator()
    return _feedback_generator_instance
