# System Architecture Overview

## 1. System Overview

A single-process Python console application for real-time voice-to-text dictation. All processing runs locally — audio capture and VAD on CPU, transcription on GPU via faster-whisper (CTranslate2/CUDA). No cloud dependencies.

**Target hardware**: Windows 11 + NVIDIA RTX 5090 (32 GB GDDR7, Blackwell sm_120)

**Distribution**: Runs from source (`python -m voice_dictation`) or as a standalone Windows binary (`voice-dictation.exe`) packaged with PyInstaller.

```
Microphone → AudioCapture → VADFilter → StreamingProcessor → Output
               (thread)       (CPU)     ┌──────────────────┐  (keystrokes or
                                        │ TranscriptionEngine│  stdout)
                                        │ (faster-whisper)   │
                                        │ (CUDA/GPU)         │
                                        └──────────────────┘
```

## 2. Components

| Component | File | Responsibility | Technology |
|-----------|------|---------------|------------|
| **AudioCapture** | `audio.py` | Continuous mic recording into thread-safe queue | sounddevice (PortAudio/WASAPI) |
| **VADFilter** | `vad.py` | Detects speech segments, filters silence | Silero VAD v6 (ONNX via faster-whisper) |
| **TranscriptionEngine** | `transcriber.py` | Converts speech audio to text on GPU | faster-whisper (CTranslate2/CUDA) |
| **StreamingProcessor** | `processor.py` | Chunked processing, local agreement, buffer management | Custom Python |
| **ConsoleOutput** | `output.py` | Renders confirmed/partial text to stdout (test mode) | sys.stdout |
| **KeyboardOutput** | `output.py` | Types text as keystrokes into focused window (default) | Win32 SendInput (ctypes) |
| **CLI** | `__main__.py` | Arg parsing, orchestration, main loop | argparse |

## 3. Data Flow

### Audio Pipeline
1. **AudioCapture** records from microphone in a sounddevice callback thread
2. Audio arrives in 100ms blocks at the device's native sample rate
3. If native rate != 16kHz, linear interpolation resampling is applied in the callback
4. Resampled float32 mono chunks are placed in a bounded `queue.Queue` (max 300)

### Processing Pipeline (Main Thread)
1. Main loop polls `AudioCapture.get_audio()` with 100ms timeout
2. Each chunk is passed to `VADFilter.is_speech()` — Silero VAD ONNX checks 512-sample windows
3. If speech detected, chunk is fed to `StreamingProcessor.feed_audio()`
4. During silence within a speech session, audio continues to be fed (preserves natural pauses)
5. After sustained silence (`min_silence_ms`, default 400ms), utterance is finalized via `processor.finish()`

### Transcription Pipeline
1. `StreamingProcessor` accumulates audio chunks in a buffer
2. Every `chunk_size` seconds (default 0.5s), full buffer is sent to `TranscriptionEngine.transcribe()`
3. faster-whisper runs Whisper inference on GPU with `beam_size=1` (greedy), `vad_filter=False`
4. Results are compared to previous transcription via **local agreement**
5. Text stable across 2 consecutive transcriptions → **confirmed** (committed)
6. Remaining unstable text → **partial** (displayed but may change)
7. Buffer is trimmed to 30s max to bound latency

### Output
- **KeyboardOutput** (default): Uses Win32 `SendInput` with `KEYEVENTF_UNICODE` scan codes. Partial text is not sent (only confirmed text is typed).
- **ConsoleOutput** (`--console`): Confirmed text is written to stdout. Partial text uses carriage return overwrite for live preview.

## 4. Threading Model

```
Main Thread:     CLI parse → Model load → Warmup → VAD load → Start audio → Main loop → Cleanup
Audio Thread:    sounddevice callback → resample → push to queue
```

- Only 2 threads: main thread and sounddevice callback thread
- Communication: bounded `queue.Queue(maxsize=300)`
- No locks needed — queue handles synchronization
- Graceful shutdown: `SIGINT` handler sets flag, main loop exits, audio stream is stopped

## 5. Streaming Strategy: Local Agreement

The local agreement algorithm (in `processor.py`) ensures output stability:

1. Audio chunks accumulate in `_audio_chunks` list
2. On each transcription cycle, full accumulated audio is transcribed
3. `_common_prefix()` finds longest word-boundary-aligned prefix shared with previous transcription
4. If common prefix extends beyond already-committed text, the new portion is **confirmed**
5. Text beyond the common prefix is **partial** (may change on next cycle)
6. On `finish()`, all remaining text is committed as final

This prevents the "flickering text" problem where Whisper revises earlier words as more context arrives.

## 6. Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| faster-whisper | >=1.1.0 | Whisper inference (CTranslate2 + CUDA) |
| sounddevice | >=0.5.0 | Real-time audio capture (PortAudio) |
| numpy | >=1.24 | Audio array processing |
| torch | >=2.0 | CUDA runtime (used by faster-whisper internals) |
| torchaudio | >=2.0 | Audio utilities (installed alongside torch) |
| onnxruntime | (via faster-whisper) | Silero VAD ONNX inference |

**Build dependency**: PyInstaller >=6.0 (for packaging only)

**System requirements**: Python 3.10+, CUDA 12.x, cuDNN 9.x, NVIDIA driver with RTX 5090 support

## 7. Packaging

The application is packaged as a standalone Windows binary using PyInstaller in one-directory mode.

| Artifact | Purpose |
|----------|---------|
| `voice_dictation.spec` | PyInstaller spec file (onedir, console, UPX disabled) |
| `build.py` | Build + verification script |
| `run.py` | Entry point wrapper (enables relative imports in frozen mode) |
| `hooks/hook-ctranslate2.py` | Collects ctranslate2 DLLs/pyds |
| `hooks/pyi_rth_faster_whisper.py` | Patches `get_assets_path()` for `sys._MEIPASS` |

**Output**: `dist/voice-dictation/` (~4.3 GB, dominated by torch CUDA DLLs)

Key packaging decisions:
- **onedir** (not onefile) — avoids slow self-extraction of multi-GB archive
- **UPX disabled** — UPX corrupts CUDA/cuDNN DLLs
- **Silero VAD via ONNX** — `torch.hub` requires Git at runtime which breaks in frozen builds; faster-whisper bundles `silero_vad_v6.onnx`
- **Models not bundled** — Whisper models download from Hugging Face on first run (~1-3 GB depending on model)

## 8. Error Handling

| Scenario | Behavior |
|----------|----------|
| No CUDA GPU | Print error + driver check suggestion, exit |
| PyTorch not installed | Print install instructions, exit |
| Microphone unavailable | List available devices, exit |
| Audio queue overflow | Oldest chunks dropped silently |
| Transcription error | Logged to stderr, processing continues |
| Ctrl+C | Flush remaining buffer, print final text, clean shutdown |
