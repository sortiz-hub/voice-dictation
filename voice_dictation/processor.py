"""Streaming processor — accumulates audio, transcribes periodically, emits text."""

import time
import numpy as np
from .transcriber import TranscriptionEngine


class StreamingProcessor:
    def __init__(self, engine: TranscriptionEngine, chunk_size: float = 1.0, sample_rate: int = 16000):
        self._engine = engine
        self._chunk_interval = chunk_size
        self._sample_rate = sample_rate

        self._audio_chunks: list[np.ndarray] = []
        self._total_samples = 0
        self._last_transcribe_time = 0.0
        self._prev_text = ""
        self._committed_text = ""

    def feed_audio(self, audio: np.ndarray) -> tuple[str | None, str]:
        """Feed an audio chunk. Returns (new_confirmed_text or None, partial_text).

        Transcription runs only when enough time has passed since the last run.
        """
        self._audio_chunks.append(audio)
        self._total_samples += len(audio)

        now = time.monotonic()
        if now - self._last_transcribe_time < self._chunk_interval:
            # Not enough time elapsed, return current partial
            return None, ""

        if self._total_samples < self._sample_rate * 0.3:
            # Less than 0.3s of audio, skip
            return None, ""

        self._last_transcribe_time = now
        return self._do_transcribe()

    def _do_transcribe(self) -> tuple[str | None, str]:
        full_audio = np.concatenate(self._audio_chunks)
        current_text = self._engine.transcribe(full_audio)

        if not current_text:
            self._prev_text = ""
            return None, ""

        # Local agreement: find common prefix with previous transcription
        confirmed_new = None
        common = _common_prefix(self._prev_text, current_text)

        if common and len(common) > len(self._committed_text):
            confirmed_new = common[len(self._committed_text):]
            self._committed_text = common

        self._prev_text = current_text
        partial = current_text[len(self._committed_text):]

        # Trim buffer if too long (keep last 30s)
        max_samples = 30 * self._sample_rate
        if self._total_samples > max_samples:
            self._trim_buffer(max_samples)

        return confirmed_new, partial

    def finish(self) -> str:
        """Flush remaining buffer, return any uncommitted text."""
        if not self._audio_chunks:
            return ""
        full_audio = np.concatenate(self._audio_chunks)
        text = self._engine.transcribe(full_audio)
        remaining = text[len(self._committed_text):] if text else ""
        self.reset()
        return remaining.strip()

    def reset(self):
        """Reset state for a new utterance."""
        self._audio_chunks.clear()
        self._total_samples = 0
        self._prev_text = ""
        self._committed_text = ""
        self._last_transcribe_time = 0.0

    def _trim_buffer(self, keep_samples: int):
        full = np.concatenate(self._audio_chunks)
        trimmed = full[-keep_samples:]
        self._audio_chunks = [trimmed]
        self._total_samples = len(trimmed)


def _common_prefix(a: str, b: str) -> str:
    """Longest common prefix, breaking at word boundaries."""
    min_len = min(len(a), len(b))
    i = 0
    while i < min_len and a[i] == b[i]:
        i += 1
    prefix = a[:i]
    last_space = prefix.rfind(" ")
    if last_space > 0 and i < min_len:
        return prefix[:last_space + 1]
    return prefix
