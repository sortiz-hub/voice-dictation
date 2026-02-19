# SPEC001 - Delivery Strategy: Local Voice Dictation System

## Phase 1: Core Pipeline (MVP)

**Goal:** Capture microphone audio, transcribe with faster-whisper on GPU, print to console. Basic but functional end-to-end dictation.

### M1.1: Project Setup & Dependencies
- **Status**: `pending`
- **Acceptance Criteria**:
  - [ ] Python project structure created (`voice_dictation/` package)
  - [ ] `requirements.txt` with all dependencies
  - [ ] `pyproject.toml` or `setup.py` for installable package
  - [ ] CUDA/cuDNN verified working on RTX 5090
  - [ ] `faster-whisper` loads a model on GPU successfully

### M1.2: Audio Capture Module
- **Status**: `pending`
- **Acceptance Criteria**:
  - [ ] `audio.py` captures real-time audio from default microphone
  - [ ] Audio is 16kHz, mono, int16 PCM
  - [ ] Audio is pushed to a thread-safe queue
  - [ ] `--list-devices` prints available input devices
  - [ ] `--device` selects a specific input device

### M1.3: Basic Transcription (Non-Streaming)
- **Status**: `pending`
- **Acceptance Criteria**:
  - [ ] `transcriber.py` wraps faster-whisper `WhisperModel`
  - [ ] Model loads on CUDA with float16
  - [ ] Fixed-size audio chunks (e.g. 5s) are transcribed and printed
  - [ ] `--model` and `--language` CLI flags work
  - [ ] End-to-end: speak into mic → text appears in console

### M1.4: VAD Integration
- **Status**: `pending`
- **Acceptance Criteria**:
  - [ ] `vad.py` wraps Silero VAD
  - [ ] Only speech segments are sent to transcription
  - [ ] No phantom/hallucinated text during silence
  - [ ] VAD parameters configurable

---

## Phase 2: Real-Time Streaming

**Goal:** Upgrade from batch processing to streaming with local agreement policy for low-latency, confirmed output.

### M2.1: Streaming Processor with Local Agreement
- **Status**: `pending`
- **Acceptance Criteria**:
  - [ ] `processor.py` implements sliding buffer + chunked processing
  - [ ] Local agreement policy: text confirmed after 2 consistent iterations
  - [ ] Audio buffer is trimmed after confirmed segments
  - [ ] `--chunk-size` configurable (default 1.0s)

### M2.2: Partial & Confirmed Output Rendering
- **Status**: `pending`
- **Acceptance Criteria**:
  - [ ] `output.py` renders confirmed text on committed lines
  - [ ] Partial (unconfirmed) text shown with carriage return overwrite
  - [ ] Clean visual distinction between confirmed and in-progress text
  - [ ] No flickering or garbled output in Windows terminal

### M2.3: Graceful Shutdown & Edge Cases
- **Status**: `pending`
- **Acceptance Criteria**:
  - [ ] Ctrl+C flushes remaining buffer text before exit
  - [ ] Audio queue overflow handled (drop oldest, warn)
  - [ ] Model load shows progress indicator
  - [ ] Startup errors (no GPU, no mic) produce helpful messages

---

## Phase 3: Polish & Optimization

**Goal:** Fine-tune performance, add quality-of-life features, ensure sub-500ms latency.

### M3.1: Latency Optimization
- **Status**: `pending`
- **Acceptance Criteria**:
  - [ ] End-to-end latency measured and documented
  - [ ] Confirmed output under 500ms with large-v3-turbo on RTX 5090
  - [ ] Partial output under 300ms
  - [ ] beam_size=1 (greedy) as default for speed
  - [ ] Warm-up transcription at startup to avoid cold-start penalty

### M3.2: Configuration & UX Polish
- **Status**: `pending`
- **Acceptance Criteria**:
  - [ ] `--compute-type` flag (float16, int8_float16, int8)
  - [ ] `--beam-size` flag
  - [ ] Startup banner shows: model, device, language, GPU info
  - [ ] `--help` documents all options clearly

---

## Summary

| Phase | Milestones | Status |
|-------|-----------|--------|
| Phase 1: Core Pipeline | M1.1 - M1.4 | `pending` |
| Phase 2: Real-Time Streaming | M2.1 - M2.3 | `pending` |
| Phase 3: Polish & Optimization | M3.1 - M3.2 | `pending` |
