"""Transcription engine wrapping faster-whisper."""

import sys
import numpy as np
from faster_whisper import WhisperModel


class TranscriptionEngine:
    def __init__(
        self,
        model_name: str = "large-v3-turbo",
        compute_type: str = "float16",
        language: str | None = None,
        beam_size: int = 1,
    ):
        self.language = language
        self.beam_size = beam_size

        print(f"Loading model '{model_name}' ({compute_type}) on CUDA...", end=" ", file=sys.stderr, flush=True)
        self._model = WhisperModel(
            model_name,
            device="cuda",
            compute_type=compute_type,
        )
        print("done.", file=sys.stderr, flush=True)

    def transcribe(self, audio: np.ndarray) -> str:
        """Transcribe audio array, return concatenated text."""
        segments, _ = self._model.transcribe(
            audio,
            beam_size=self.beam_size,
            language=self.language,
            vad_filter=False,  # we handle VAD externally
            without_timestamps=True,
            condition_on_previous_text=False,
        )
        return "".join(s.text for s in segments).strip()

    def warmup(self) -> None:
        """Run a short transcription to warm up the model."""
        silence = np.zeros(16000, dtype=np.float32)  # 1 second of silence
        self.transcribe(silence)
