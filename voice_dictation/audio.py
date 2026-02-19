"""Audio capture from microphone using sounddevice."""

import queue
import numpy as np
import sounddevice as sd


def _resample(audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
    """Simple linear interpolation resampling."""
    if orig_sr == target_sr:
        return audio
    ratio = target_sr / orig_sr
    n_samples = int(len(audio) * ratio)
    indices = np.arange(n_samples) / ratio
    indices = np.clip(indices, 0, len(audio) - 1)
    idx_floor = indices.astype(np.int64)
    idx_ceil = np.minimum(idx_floor + 1, len(audio) - 1)
    frac = (indices - idx_floor).astype(np.float32)
    return audio[idx_floor] * (1 - frac) + audio[idx_ceil] * frac


class AudioCapture:
    TARGET_SR = 16000  # Whisper requires 16kHz

    def __init__(self, device: int | None = None, sample_rate: int = 16000, block_duration_ms: int = 100):
        self.device = device
        self._target_sr = sample_rate
        # Query the device's native sample rate
        dev_info = sd.query_devices(device or sd.default.device[0], kind="input")
        self._native_sr = int(dev_info["default_samplerate"])
        self._needs_resample = self._native_sr != self._target_sr
        self.block_size = int(self._native_sr * block_duration_ms / 1000)
        self._queue: queue.Queue[np.ndarray] = queue.Queue(maxsize=300)
        self._stream: sd.InputStream | None = None

    def _callback(self, indata: np.ndarray, frames: int, time_info, status):
        if status:
            pass  # drop warning, keep going
        audio = indata[:, 0].copy()
        if self._needs_resample:
            audio = _resample(audio, self._native_sr, self._target_sr)
        self._queue.put(audio)

    def start(self) -> None:
        self._stream = sd.InputStream(
            samplerate=self._native_sr,
            blocksize=self.block_size,
            device=self.device,
            dtype="float32",
            channels=1,
            callback=self._callback,
        )
        self._stream.start()

    def get_audio(self, timeout: float = 0.1) -> np.ndarray | None:
        try:
            return self._queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def stop(self) -> None:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

    @staticmethod
    def list_devices() -> list[dict]:
        devices = sd.query_devices()
        hostapis = sd.query_hostapis()
        # Prefer WASAPI on Windows (lowest latency), fall back to first available
        wasapi_idx = None
        for idx, api in enumerate(hostapis):
            if "WASAPI" in api["name"]:
                wasapi_idx = idx
                break

        result = []
        default_input = sd.default.device[0] if isinstance(sd.default.device, tuple) else sd.default.device
        for i, d in enumerate(devices):
            if d["max_input_channels"] > 0:
                if wasapi_idx is not None and d["hostapi"] != wasapi_idx:
                    continue
                result.append({
                    "index": i,
                    "name": d["name"],
                    "channels": d["max_input_channels"],
                    "default": i == default_input,
                })
        return result
