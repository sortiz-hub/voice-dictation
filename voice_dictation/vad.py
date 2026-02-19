"""Voice Activity Detection using Silero VAD."""

import numpy as np
import torch


class VADFilter:
    def __init__(self, threshold: float = 0.5, sample_rate: int = 16000):
        self.threshold = threshold
        self.sample_rate = sample_rate

        self._model, _ = torch.hub.load(
            repo_or_dir="snakers4/silero-vad",
            model="silero_vad",
            trust_repo=True,
        )
        self._model.eval()

    def is_speech(self, audio: np.ndarray) -> bool:
        """Check if audio chunk contains speech."""
        tensor = torch.from_numpy(audio).float()
        window_size = 512
        for i in range(0, len(tensor), window_size):
            window = tensor[i:i + window_size]
            if len(window) < window_size:
                window = torch.nn.functional.pad(window, (0, window_size - len(window)))
            prob = self._model(window, self.sample_rate).item()
            if prob >= self.threshold:
                return True
        return False

    def reset(self) -> None:
        self._model.reset_states()
