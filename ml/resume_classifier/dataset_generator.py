"""
ml/resume_classifier/dataset_generator.py
-------------------------------------------
Generates a labeled training dataset for the resume classification model.
Belongs in: ml/resume_classifier/dataset_generator.py

NOTE: No real-world labeled resume dataset was provided with the project
report, so this script builds a representative synthetic dataset from
domain skill/keyword templates (a common, accepted approach for a
final-year academic ML pipeline). To use a REAL dataset instead (e.g. the
public "Resume Dataset" on Kaggle), replace `build_dataset()` with a
pandas.read_csv() call that returns a DataFrame with the same
['text', 'category'] columns, and re-run train_model.py.

Run directly to (re)generate dataset/resume_dataset.csv:
    python dataset_generator.py
"""

import random
import pandas as pd

random.seed(42)

# Category -> representative skills/keywords/phrases seen in that domain's resumes
CATEGORY_TEMPLATES = {
    "Data Science": [
        "python", "pandas", "numpy", "scikit-learn", "machine learning",
        "deep learning", "tensorflow", "pytorch", "data visualization",
        "statistics", "sql", "jupyter notebook", "feature engineering",
        "regression", "classification", "clustering", "a/b testing",
    ],
    "Web Development": [
        "html", "css", "javascript", "react.js", "node.js", "express",
        "rest api", "mongodb", "mysql", "responsive design", "typescript",
        "next.js", "redux", "webpack", "frontend", "backend", "full stack",
    ],
    "Generative AI / LLM Engineering": [
        "llm", "large language models", "prompt engineering", "rag",
        "retrieval augmented generation", "langchain", "vector database",
        "gemini api", "openai api", "fine-tuning", "embeddings",
        "transformers", "huggingface", "generative ai", "chatbot",
    ],
    "DevOps / Cloud Engineering": [
        "docker", "kubernetes", "aws", "azure", "gcp", "ci/cd", "jenkins",
        "terraform", "ansible", "linux", "microservices", "monitoring",
        "cloud infrastructure", "helm", "prometheus", "grafana",
    ],
    "UI/UX Design": [
        "figma", "adobe xd", "wireframing", "prototyping", "user research",
        "usability testing", "design systems", "interaction design",
        "visual design", "sketch", "user personas", "information architecture",
    ],
    "Mobile Development": [
        "android", "kotlin", "swift", "flutter", "react native", "ios",
        "mobile ui", "firebase", "xcode", "android studio", "app store",
        "play store deployment", "mobile architecture",
    ],
    "Database Administration": [
        "postgresql", "mysql", "oracle", "database design", "indexing",
        "query optimization", "backup and recovery", "replication",
        "stored procedures", "normalization", "sql server", "pgadmin",
    ],
}

FILLER_PHRASES = [
    "Worked on multiple projects involving {skill}.",
    "Strong hands-on experience with {skill}.",
    "Completed coursework and certification in {skill}.",
    "Built and deployed applications using {skill}.",
    "Collaborated with a team to deliver solutions using {skill}.",
    "Proficient in {skill} with practical project experience.",
]


def _generate_resume_text(category: str, num_skills: int = 8) -> str:
    skills = random.sample(CATEGORY_TEMPLATES[category], k=min(num_skills, len(CATEGORY_TEMPLATES[category])))
    sentences = [random.choice(FILLER_PHRASES).format(skill=skill) for skill in skills]
    random.shuffle(sentences)
    return " ".join(sentences)


def build_dataset(samples_per_category: int = 120) -> pd.DataFrame:
    """Builds a synthetic ['text', 'category'] DataFrame for training."""
    rows = []
    for category in CATEGORY_TEMPLATES:
        for _ in range(samples_per_category):
            num_skills = random.randint(4, 10)
            text = _generate_resume_text(category, num_skills)
            rows.append({"text": text, "category": category})
    df = pd.DataFrame(rows).sample(frac=1, random_state=42).reset_index(drop=True)
    return df


if __name__ == "__main__":
    dataset = build_dataset()
    dataset.to_csv("dataset/resume_dataset.csv", index=False)
    print(f"Generated {len(dataset)} rows across {dataset['category'].nunique()} categories")
    print(dataset['category'].value_counts())
