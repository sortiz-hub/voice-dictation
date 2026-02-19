"""Voice Activity Detection using Silero VAD (ONNX via faster-whisper)."""

import numpy as np


class VADFilter:
    def __init__(self, threshold: float = 0.5, sample_rate: int = 16000):
        self.threshold = threshold
        self.sample_rate = sample_rate
        self._window_size = 512

        from faster_whisper.vad import get_vad_model
        self._model = get_vad_model()

    def is_speech(self, audio: np.ndarray) -> bool:
        """Check if audio chunk contains speech."""
        # Pad to multiple of window_size
        remainder = len(audio) % self._window_size
        if remainder != 0:
            audio = np.pad(audio, (0, self._window_size - remainder))

        # SileroVADModel.__call__ returns shape (num_windows, 1)
        probs = self._model(audio, num_samples=self._window_size)
        return bool(np.any(probs >= self.threshold))

    def reset(self) -> None:
        # ONNX model resets h/c to zeros on each __call__, no persistent state
        pass
