"""
ml/resume_parser/parser.py
---------------------------
Resume Parsing Module.
Belongs in: ml/resume_parser/parser.py

Pipeline:
    1. PyMuPDF (fitz)  -> extract raw text from the uploaded PDF resume.
    2. spaCy            -> tokenize / clean text, base NLP pipeline.
    3. SkillNER          -> extract structured technical & soft skills from text
                            using spaCy's NER pipeline + a skills database.
    4. Sentence-Transformers -> encode the resume text into a dense embedding
                            vector, used later for resume<->job semantic
                            matching (job recommendation) and dedup/search.

Called by: backend/app/services/resume_service.py
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

import fitz  # PyMuPDF
import spacy
from sentence_transformers import SentenceTransformer

try:
    from skillNer.general_params import SKILL_DB
    from skillNer.skill_extractor_class import SkillExtractor
    from spacy.matcher import PhraseMatcher

    _SKILLNER_AVAILABLE = True
except Exception:
    # SkillNER + its skill DB are heavy optional downloads; the parser still
    # works with a regex-based fallback skill list if they aren't installed.
    _SKILLNER_AVAILABLE = False


# A compact fallback keyword bank used if SkillNER isn't available in the
# environment. In production, SkillNER's SKILL_DB (2,000+ skills) is used.
FALLBACK_SKILLS = [
    "python", "java", "javascript", "typescript", "c++", "c#", "sql", "nosql",
    "react", "react.js", "vue", "angular", "node.js", "express", "django",
    "flask", "fastapi", "spring boot", "postgresql", "mysql", "mongodb",
    "docker", "kubernetes", "aws", "azure", "gcp", "git", "github", "ci/cd",
    "machine learning", "deep learning", "nlp", "computer vision",
    "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
    "llm", "large language models", "prompt engineering", "rag",
    "generative ai", "data structures", "algorithms", "rest api",
    "microservices", "html", "css", "tailwind css", "figma", "ui/ux",
]


@dataclass
class ParsedResume:
    raw_text: str
    cleaned_text: str
    extracted_skills: List[str] = field(default_factory=list)
    embedding: List[float] = field(default_factory=list)


class ResumeParser:
    """
    Loads spaCy + Sentence-Transformer models once and reuses them across
    requests (model loading is expensive — do NOT instantiate per-request).
    """

    def __init__(
        self,
        spacy_model: str = "en_core_web_sm",
        embedding_model: str = "all-MiniLM-L6-v2",
    ):
        self.nlp = spacy.load(spacy_model)
        self.embedder = SentenceTransformer(embedding_model)

        self.skill_extractor = None
        if _SKILLNER_AVAILABLE:
            try:
                self.skill_extractor = SkillExtractor(self.nlp, SKILL_DB, PhraseMatcher)
            except Exception:
                self.skill_extractor = None

    # ------------------------------------------------------------------
    # Step 1: Text extraction (PyMuPDF)
    # ------------------------------------------------------------------
    @staticmethod
    def extract_text_from_pdf(file_path: str) -> str:
        """Extract raw text from a PDF resume using PyMuPDF."""
        text_parts = []
        with fitz.open(file_path) as doc:
            for page in doc:
                text_parts.append(page.get_text())
        return "\n".join(text_parts)

    @staticmethod
    def clean_text(raw_text: str) -> str:
        """Basic whitespace/artifact cleanup prior to NLP processing."""
        text = re.sub(r"\s+", " ", raw_text)
        text = re.sub(r"[•●▪]", " ", text)
        return text.strip()

    # ------------------------------------------------------------------
    # Step 2 + 3: Skill extraction (spaCy + SkillNER, with regex fallback)
    # ------------------------------------------------------------------
    def extract_skills(self, cleaned_text: str) -> List[str]:
        if self.skill_extractor is not None:
            try:
                annotations = self.skill_extractor.annotate(cleaned_text)
                full_matches = [m["doc_node_value"] for m in annotations["results"]["full_matches"]]
                ngram_matches = [m["doc_node_value"] for m in annotations["results"]["ngram_scored"]]
                skills = {s.lower().strip() for s in full_matches + ngram_matches}
                if skills:
                    return sorted(skills)
            except Exception:
                pass  # fall through to regex fallback below

        # Regex fallback — keyword-matches against FALLBACK_SKILLS
        lowered = cleaned_text.lower()
        found = {skill for skill in FALLBACK_SKILLS if skill in lowered}
        return sorted(found)

    # ------------------------------------------------------------------
    # Step 4: Sentence embedding (for job-matching / dedup / search)
    # ------------------------------------------------------------------
    def embed(self, cleaned_text: str) -> List[float]:
        vector = self.embedder.encode(cleaned_text, normalize_embeddings=True)
        return vector.tolist()

    # ------------------------------------------------------------------
    # Full pipeline
    # ------------------------------------------------------------------
    def parse(self, file_path: str) -> ParsedResume:
        raw_text = self.extract_text_from_pdf(file_path)
        cleaned_text = self.clean_text(raw_text)
        skills = self.extract_skills(cleaned_text)
        embedding = self.embed(cleaned_text)
        return ParsedResume(
            raw_text=raw_text,
            cleaned_text=cleaned_text,
            extracted_skills=skills,
            embedding=embedding,
        )


# Module-level singleton so FastAPI doesn't reload the models on every request
_parser_instance: ResumeParser | None = None


def get_resume_parser() -> ResumeParser:
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = ResumeParser()
    return _parser_instance
