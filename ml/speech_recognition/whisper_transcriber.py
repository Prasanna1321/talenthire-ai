"""
ml/speech_recognition/whisper_transcriber.py
------------------------------------------------
Speech Recognition Module.
Belongs in: ml/speech_recognition/whisper_transcriber.py

Uses OpenAI's Whisper (open-source, run locally — no external API call)
to transcribe a candidate's recorded interview-answer audio into text,
per the report's "Speech Recognition Module" (captures spoken responses
and converts them to text for further NLP evaluation).
"""

from __future__ import annotations

from dataclasses import dataclass

import whisper


@dataclass
class TranscriptionResult:
    text: str
    language: str
    duration_seconds: float


class WhisperTranscriber:
    """
    Loads a Whisper model once (default: 'base' — good balance of speed vs
    accuracy for short interview answers on CPU). Use 'small' or 'medium'
    for better accuracy if a GPU is available.
    """

    def __init__(self, model_size: str = "base"):
        self.model = whisper.load_model(model_size)

    def transcribe(self, audio_file_path: str) -> TranscriptionResult:
        result = self.model.transcribe(audio_file_path, fp16=False)
        segments = result.get("segments", [])
        duration = segments[-1]["end"] if segments else 0.0
        return TranscriptionResult(
            text=result["text"].strip(),
            language=result.get("language", "en"),
            duration_seconds=duration,
        )


_transcriber_instance: WhisperTranscriber | None = None


def get_transcriber() -> WhisperTranscriber:
    global _transcriber_instance
    if _transcriber_instance is None:
        _transcriber_instance = WhisperTranscriber()
    return _transcriber_instance
