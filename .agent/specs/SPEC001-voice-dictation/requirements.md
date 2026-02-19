# SPEC001 - Local Voice Dictation System

## 1. Purpose & Scope

### 1.1 Problem Statement

Developers and professionals need fast, private, real-time voice-to-text dictation that runs entirely on local hardware. Cloud-based solutions introduce latency, privacy concerns, and ongoing costs. The RTX 5090 (32 GB GDDR7, 21,760 CUDA cores, 680 5th-gen Tensor Cores) is massively overpowered for speech-to-text, enabling the use of the largest and most accurate models with near-zero latency.

### 1.2 Scope

Build a Python console application for Windows 11 that:
- Captures microphone audio in real-time
- Transcribes speech using the fastest local Whisper-based models on GPU
- Outputs transcribed text directly to the console (stdout)
- Runs 100% locally with no cloud dependencies

### 1.3 Out of Scope

- GUI / desktop application (console only for v1)
- Speaker diarization
- Translation (transcription only)
- Multi-GPU support
- Mobile or cross-platform deployment
- Integration with other applications (clipboard, editors) beyond stdout

---

## 2. Actors & User Stories

### 2.1 Actors

| Actor | Description |
|-------|-------------|
| **Dictator** | A person speaking into a microphone who wants their speech transcribed in real-time |

### 2.2 User Stories

| ID | Actor | Story | Priority |
|----|-------|-------|----------|
| US-01 | Dictator | As a dictator, I want to start the application and immediately begin speaking, so that my words appear as text in the console with minimal delay | Must |
| US-02 | Dictator | As a dictator, I want silence to be automatically detected, so that only my speech is processed and no phantom text appears during pauses | Must |
| US-03 | Dictator | As a dictator, I want to choose my audio input device, so that I can use my preferred microphone | Should |
| US-04 | Dictator | As a dictator, I want to select the Whisper model variant (turbo, large-v3, distil-large-v3), so that I can trade off speed vs accuracy | Should |
| US-05 | Dictator | As a dictator, I want to set the language explicitly or use auto-detection, so that transcription accuracy is maximized for my language | Should |
| US-06 | Dictator | As a dictator, I want to stop dictation cleanly with Ctrl+C, so that any buffered text is flushed before exit | Must |
| US-07 | Dictator | As a dictator, I want to see real-time partial (unconfirmed) transcription, so that I get immediate feedback while speaking | Should |

---

## 3. Functional Requirements

### FR-01: Audio Capture (US-01, US-03)

| ID | Requirement |
|----|-------------|
| FR-01.1 | System shall capture audio from the system microphone at 16 kHz, mono, 16-bit signed integer PCM |
| FR-01.2 | System shall list available audio input devices and allow selection via CLI argument |
| FR-01.3 | System shall default to the system default audio input device |
| FR-01.4 | Audio capture shall run in a dedicated thread/async task to prevent blocking transcription |

### FR-02: Voice Activity Detection (US-02)

| ID | Requirement |
|----|-------------|
| FR-02.1 | System shall use Silero VAD to detect speech segments in the audio stream |
| FR-02.2 | System shall only send audio chunks containing speech to the transcription engine |
| FR-02.3 | VAD shall be configurable: speech threshold, min silence duration, min speech duration |
| FR-02.4 | Default VAD parameters shall be tuned for dictation (speech_threshold=0.5, min_silence_duration_ms=600) |

### FR-03: Transcription Engine (US-01, US-04, US-05)

| ID | Requirement |
|----|-------------|
| FR-03.1 | System shall use `faster-whisper` with CTranslate2 backend for GPU inference |
| FR-03.2 | Default model shall be `large-v3-turbo` with `float16` compute type on CUDA |
| FR-03.3 | System shall support models: `tiny`, `base`, `small`, `medium`, `large-v2`, `large-v3`, `large-v3-turbo`, `distil-large-v3` |
| FR-03.4 | System shall support language code specification via `--language` flag (default: auto-detect) |
| FR-03.5 | System shall use beam_size=1 for lowest latency in real-time mode |
| FR-03.6 | System shall pre-load the model at startup before audio capture begins |
| FR-03.7 | System shall process audio in a streaming fashion using chunked processing with local agreement policy for confirmed output |

### FR-04: Streaming Output (US-01, US-06, US-07)

| ID | Requirement |
|----|-------------|
| FR-04.1 | Confirmed (stable) transcription shall be printed to stdout immediately |
| FR-04.2 | Partial (unconfirmed) transcription shall be displayed using carriage return overwrite on the same line |
| FR-04.3 | When partial text is confirmed, it shall be committed to a new line |
| FR-04.4 | On Ctrl+C (SIGINT), system shall flush any remaining buffered text and exit cleanly |

### FR-05: Configuration & CLI (US-03, US-04, US-05)

| ID | Requirement |
|----|-------------|
| FR-05.1 | CLI shall accept: `--model`, `--language`, `--device` (audio), `--chunk-size`, `--beam-size`, `--compute-type` |
| FR-05.2 | `--list-devices` shall print available audio input devices and exit |
| FR-05.3 | `--chunk-size` shall control the minimum audio chunk size in seconds (default: 1.0) |

---

## 4. Non-Functional Requirements

### NFR-01: Latency

| ID | Requirement |
|----|-------------|
| NFR-01.1 | End-to-end latency (speech to text on screen) shall be under 500ms for confirmed output on RTX 5090 with large-v3-turbo |
| NFR-01.2 | Partial output shall appear within 300ms of speech |

### NFR-02: Resource Usage

| ID | Requirement |
|----|-------------|
| NFR-02.1 | VRAM usage shall not exceed 8 GB with large-v3-turbo in float16 |
| NFR-02.2 | CPU usage for audio capture and VAD shall remain under 10% of a single core |

### NFR-03: Accuracy

| ID | Requirement |
|----|-------------|
| NFR-03.1 | Transcription WER shall be equivalent to faster-whisper benchmarks for the selected model |
| NFR-03.2 | System shall produce no phantom text during silence (VAD must prevent hallucination) |

### NFR-04: Startup

| ID | Requirement |
|----|-------------|
| NFR-04.1 | Model loading shall display a progress indicator |
| NFR-04.2 | First transcription shall be available within 5 seconds of model load completing |

---

## 5. Constraints & Assumptions

### Constraints

- Windows 11 with NVIDIA RTX 5090 (32 GB GDDR7)
- CUDA 12.x + cuDNN 9.x must be installed
- Python 3.10+
- No internet connection required after initial model download

### Assumptions

- User has a working microphone connected to the system
- NVIDIA drivers are up to date with CUDA 12 support
- faster-whisper and its dependencies are compatible with the RTX 5090 (Blackwell architecture)

---

## 6. Technology Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Language | Python 3.10+ | Ecosystem support for all ML libraries |
| STT Engine | faster-whisper (CTranslate2) | 4x faster than openai/whisper, lower VRAM, mature API |
| Default Model | large-v3-turbo | 6x faster than large-v3, minimal accuracy loss, best speed/accuracy tradeoff |
| VAD | Silero VAD (built into faster-whisper) | Proven, lightweight, prevents hallucination on silence |
| Audio Capture | sounddevice (PortAudio) | Cross-platform, low-latency, simple Python API for real-time audio |
| Streaming Strategy | Chunked processing with local agreement | Proven approach from whisper_streaming, confirms stable output |
| Compute | float16 on CUDA | Best throughput on RTX 5090 Tensor Cores |
