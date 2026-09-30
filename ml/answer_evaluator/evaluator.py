"""
ml/answer_evaluator/evaluator.py
------------------------------------
Answer Evaluation Module.
Belongs in: ml/answer_evaluator/evaluator.py

Evaluates a candidate's transcribed answer against the question's
`ideal_answer` reference text using:
    1. Sentence-Transformers -> embed both texts
    2. Cosine similarity      -> semantic closeness score (0-1)
    3. Lightweight NLP heuristics -> relevance / fluency / confidence
       sub-scores that combine with similarity into a final weighted score.

This mirrors the report's "Response Analysis and Feedback Module": NLP +
Generative AI analyze answer relevance, communication quality, and produce
a score used later for the feedback report.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import numpy as np
from sentence_transformers import SentenceTransformer, util


@dataclass
class EvaluationResult:
    similarity_score: float     # 0-1, raw cosine similarity
    relevance_score: float      # 0-100
    fluency_score: float        # 0-100
    confidence_score: float     # 0-100
    final_score: float          # 0-100, weighted aggregate


# Weighting rationale: semantic relevance matters most for a technical
# answer, fluency/confidence are secondary signals from the text itself
# (a fuller NLP pipeline could add prosody features from the raw audio).
WEIGHTS = {
    "relevance": 0.55,
    "fluency": 0.25,
    "confidence": 0.20,
}

FILLER_WORDS = {"um", "uh", "like", "you know", "sort of", "kind of", "basically", "actually"}


class AnswerEvaluator:
    def __init__(self, embedding_model: str = "all-MiniLM-L6-v2"):
        self.embedder = SentenceTransformer(embedding_model)

    # ------------------------------------------------------------------
    def _cosine_similarity(self, answer_text: str, ideal_answer: str) -> float:
        emb_answer = self.embedder.encode(answer_text, convert_to_tensor=True)
        emb_ideal = self.embedder.encode(ideal_answer, convert_to_tensor=True)
        score = util.cos_sim(emb_answer, emb_ideal).item()
        return max(0.0, min(1.0, score))  # clip to [0,1]

    # ------------------------------------------------------------------
    def _fluency_heuristic(self, answer_text: str) -> float:
        """
        Cheap proxy for fluency from text alone: penalizes filler words,
        very short answers, and heavy repetition. Scored 0-100.
        """
        words = re.findall(r"\b\w+\b", answer_text.lower())
        if not words:
            return 0.0

        word_count = len(words)
        filler_count = sum(1 for w in words if w in FILLER_WORDS)
        filler_ratio = filler_count / word_count

        unique_ratio = len(set(words)) / word_count

        length_score = min(1.0, word_count / 60)  # answers under ~60 words score lower
        fluency = (1 - filler_ratio) * 0.5 + unique_ratio * 0.3 + length_score * 0.2
        return round(max(0.0, min(1.0, fluency)) * 100, 2)

    # ------------------------------------------------------------------
    def _confidence_heuristic(self, answer_text: str) -> float:
        """
        Cheap proxy for confidence: fewer hedging phrases ("I think maybe",
        "I'm not sure", "probably") -> higher confidence score.
        """
        hedges = ["i think", "maybe", "i'm not sure", "probably", "i guess", "not certain"]
        lowered = answer_text.lower()
        hedge_hits = sum(lowered.count(h) for h in hedges)
        base = 100 - (hedge_hits * 15)
        return round(max(0.0, min(100.0, base)), 2)

    # ------------------------------------------------------------------
    def evaluate(self, answer_text: str, ideal_answer: str) -> EvaluationResult:
        if not answer_text.strip():
            return EvaluationResult(0.0, 0.0, 0.0, 0.0, 0.0)

        similarity = self._cosine_similarity(answer_text, ideal_answer) if ideal_answer else 0.5
        relevance = round(similarity * 100, 2)
        fluency = self._fluency_heuristic(answer_text)
        confidence = self._confidence_heuristic(answer_text)

        final = (
            relevance * WEIGHTS["relevance"]
            + fluency * WEIGHTS["fluency"]
            + confidence * WEIGHTS["confidence"]
        )

        return EvaluationResult(
            similarity_score=round(similarity, 4),
            relevance_score=relevance,
            fluency_score=fluency,
            confidence_score=confidence,
            final_score=round(final, 2),
        )


_evaluator_instance: AnswerEvaluator | None = None


def get_answer_evaluator() -> AnswerEvaluator:
    global _evaluator_instance
    if _evaluator_instance is None:
        _evaluator_instance = AnswerEvaluator()
    return _evaluator_instance
