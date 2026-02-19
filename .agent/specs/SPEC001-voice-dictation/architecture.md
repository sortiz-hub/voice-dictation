# SPEC001 - Architecture: Local Voice Dictation System

## 1. System Overview

A single-process Python console application with three concurrent pipelines: audio capture, voice activity detection, and transcription. All processing runs locally on the RTX 5090 GPU (transcription) and CPU (audio capture, VAD).

```
Microphone → Audio Capture Thread → VAD Filter → Transcription Engine → Console Output
                (sounddevice)        (Silero)     (faster-whisper/CUDA)    (stdout)
```

## 2. Component Architecture

### 2.1 Components

| Component | Responsibility | Technology |
|-----------|---------------|------------|
| **AudioCapture** | Continuous mic recording into a thread-safe audio buffer | `sounddevice` (PortAudio) |
| **VADFilter** | Detects speech segments, filters silence, prevents hallucination | Silero VAD via `torch` |
| **TranscriptionEngine** | Converts speech audio chunks to text using Whisper on GPU | `faster-whisper` (CTranslate2/CUDA) |
| **StreamingProcessor** | Manages chunked processing, local agreement, and output confirmation | Custom (inspired by whisper_streaming) |
| **ConsoleOutput** | Renders confirmed and partial text to stdout | Python built-in (sys.stdout) |
| **CLI** | Parses arguments, orchestrates startup and shutdown | `argparse` |

### 2.2 Data Flow

```
┌──────────────┐    raw PCM     ┌──────────────┐   speech chunks  ┌─────────────────────┐
│ AudioCapture │───────────────>│  VADFilter    │────────────────>│ StreamingProcessor  │
│  (thread)    │  16kHz/mono    │  (Silero)     │  timestamped    │                     │
└──────────────┘   int16        └──────────────┘                  │  ┌───────────────┐  │
                                                                  │  │ Transcription │  │
                                                                  │  │   Engine      │  │
                                                                  │  │ (faster-      │  │
                                                                  │  │  whisper GPU) │  │
                                                                  │  └───────────────┘  │
                                                                  │                     │
                                                                  │  local agreement    │
                                                                  │  policy             │
                                                                  └──────────┬──────────┘
                                                                             │
                                                                   confirmed │ partial
                                                                      text   │  text
                                                                             v
                                                                  ┌─────────────────┐
                                                                  │ ConsoleOutput   │
                                                                  │ (stdout)        │
                                                                  └─────────────────┘
```

### 2.3 Threading Model

```
Main Thread:          CLI parse → Model load → Start audio → Processing loop → Cleanup
Audio Thread:         sounddevice callback → push to queue (thread-safe)
Processing (main):    pull from queue → VAD → transcribe → output
```

- **Audio capture** runs in a background thread managed by `sounddevice.InputStream` callback
- **VAD + Transcription + Output** run on the main thread in a processing loop
- Communication via `queue.Queue` (thread-safe, bounded)

### 2.4 Streaming Strategy: Local Agreement

The system uses a chunked processing approach inspired by whisper_streaming:

1. Audio is accumulated in a sliding buffer
2. Every `chunk_size` seconds (default 1s), the buffer is sent to faster-whisper
3. The system compares consecutive transcription outputs
4. Text that is consistent across 2 consecutive iterations is **confirmed** (committed)
5. Remaining text is displayed as **partial** (overwritten on next update)
6. The audio buffer is trimmed after confirmed segments to keep processing fast

This ensures:
- Low latency: partial text appears immediately
- High accuracy: only agreed-upon text is committed
- Bounded memory: buffer doesn't grow indefinitely

## 3. Project Structure

```
C:\dev\voice\
├── voice_dictation/
│   ├── __init__.py
│   ├── __main__.py          # Entry point, CLI parsing
│   ├── audio.py             # AudioCapture: mic recording with sounddevice
│   ├── vad.py               # VADFilter: Silero VAD wrapper
│   ├── transcriber.py       # TranscriptionEngine: faster-whisper wrapper
│   ├── processor.py         # StreamingProcessor: local agreement, buffer management
│   └── output.py            # ConsoleOutput: confirmed/partial text rendering
├── requirements.txt
├── setup.py                 # or pyproject.toml
└── .agent/
    └── specs/
        └── SPEC001-voice-dictation/
```

## 4. Key Interfaces

### 4.1 AudioCapture

```python
class AudioCapture:
    def __init__(self, device: int | None = None, sample_rate: int = 16000):
        """Initialize audio capture from specified or default device."""

    def start(self) -> None:
        """Begin capturing audio in background thread."""

    def get_audio(self, timeout: float = 0.1) -> np.ndarray | None:
        """Get next audio chunk from queue. Returns None on timeout."""

    def stop(self) -> None:
        """Stop capture and release resources."""

    @staticmethod
    def list_devices() -> list[dict]:
        """List available input devices."""
```

### 4.2 VADFilter

```python
class VADFilter:
    def __init__(self, threshold: float = 0.5, min_silence_ms: int = 600, min_speech_ms: int = 250):
        """Initialize Silero VAD model."""

    def process(self, audio: np.ndarray) -> list[dict]:
        """Return list of speech segments: [{'start': int, 'end': int, 'audio': np.ndarray}]"""

    def reset(self) -> None:
        """Reset VAD state for new session."""
```

### 4.3 TranscriptionEngine

```python
class TranscriptionEngine:
    def __init__(self, model_name: str = "large-v3-turbo", compute_type: str = "float16",
                 language: str | None = None, beam_size: int = 1):
        """Load faster-whisper model onto GPU."""

    def transcribe(self, audio: np.ndarray) -> list[Segment]:
        """Transcribe audio array, return segments with text and timestamps."""
```

### 4.4 StreamingProcessor

```python
class StreamingProcessor:
    def __init__(self, engine: TranscriptionEngine, chunk_size: float = 1.0):
        """Initialize streaming processor with local agreement policy."""

    def insert_audio(self, audio: np.ndarray) -> None:
        """Add audio to the processing buffer."""

    def process(self) -> tuple[str, str]:
        """Process current buffer. Returns (confirmed_text, partial_text)."""

    def finish(self) -> str:
        """Flush remaining buffer and return final text."""
```

## 5. Dependencies

```
faster-whisper>=1.1.0      # Whisper inference engine (includes CTranslate2, Silero VAD)
sounddevice>=0.5.0         # Real-time audio capture via PortAudio
numpy>=1.24                # Audio array processing
torch>=2.0                 # Required for Silero VAD
```

### System Requirements

- Python 3.10+
- CUDA 12.x toolkit
- cuDNN 9.x
- cuBLAS for CUDA 12
- NVIDIA RTX 5090 driver (latest)

## 6. Configuration Defaults

| Parameter | Default | Rationale |
|-----------|---------|-----------|
| model | large-v3-turbo | Best speed/accuracy; 6x faster than large-v3 |
| compute_type | float16 | Leverages RTX 5090 Tensor Cores |
| beam_size | 1 | Minimum latency for real-time; greedy decoding |
| chunk_size | 1.0s | Balance between latency and context |
| language | None (auto) | Convenience; explicit is faster |
| sample_rate | 16000 Hz | Whisper's native sample rate |
| vad_threshold | 0.5 | Silero default, good balance |
| min_silence_ms | 600 | Prevents premature cutoff in dictation pauses |

## 7. Error Handling

| Scenario | Handling |
|----------|----------|
| No CUDA GPU found | Print error, suggest checking drivers, exit |
| Microphone not available | Print error with available devices, exit |
| Model download fails | Print error with manual download instructions, exit |
| Audio queue overflow | Drop oldest chunks, log warning |
| Transcription error | Log error, continue processing next chunk |
| Ctrl+C | Flush buffer via `finish()`, print final text, clean shutdown |
