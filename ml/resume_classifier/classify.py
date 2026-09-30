"""
ml/resume_classifier/classify.py
-----------------------------------
Resume Classification Module - inference wrapper.
Belongs in: ml/resume_classifier/classify.py

Loads the trained resume_model.pkl (TF-IDF + RandomForest pipeline) once
and exposes a simple predict() function used by the backend resume_service.
"""

import os
import joblib
from dataclasses import dataclass

MODEL_PATH = os.path.join(os.path.dirname(__file__), "resume_model.pkl")


@dataclass
class ClassificationResult:
    predicted_category: str
    confidence: float


class ResumeClassifier:
    def __init__(self, model_path: str = MODEL_PATH):
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"resume_model.pkl not found at {model_path}. "
                f"Run dataset_generator.py then train_model.py first."
            )
        self.pipeline = joblib.load(model_path)

    def predict(self, resume_text: str) -> ClassificationResult:
        predicted_label = self.pipeline.predict([resume_text])[0]
        probabilities = self.pipeline.predict_proba([resume_text])[0]
        confidence = float(max(probabilities))
        return ClassificationResult(predicted_category=predicted_label, confidence=confidence)


_classifier_instance: ResumeClassifier | None = None


def get_resume_classifier() -> ResumeClassifier:
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = ResumeClassifier()
    return _classifier_instance
