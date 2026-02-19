# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**For comprehensive project documentation**, see **`.agent/README.md`** which indexes all architecture, SOPs, and specifications.

---

## Quick Commands

### Run
- `python -m voice_dictation` - Start dictation in keyboard mode (distil-large-v3, en, low-latency defaults)
- `python -m voice_dictation --console` - Console test mode: print transcription to stdout instead of typing
- `python -m voice_dictation --list-devices` - List available audio input devices
- `python -m voice_dictation --model large-v3-turbo --language es` - Example: different model/language

### Install
```bash
# 1. Create venv
python -m venv .venv && .venv/Scripts/activate

# 2. Install CUDA 12.8 PyTorch (required for RTX 5090 Blackwell sm_120)
pip install --pre torch torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128

# 3. Install project
pip install -e .
```

**DO NOT RUN** `pip install torch` without the CUDA 12.8 index URL — it will install CPU-only PyTorch.

---

## AI Behavior Guidelines

### Git Operations
- **DO NOT** propose or attempt git commit operations unless requested
- **DO NOT** run destructive git commands unless explicitly requested

### Documentation Usage
Before answering architecture questions or implementing features:

1. **READ `.agent/system/architecture/`** for:
   - [overview.md](/.agent/system/architecture/overview.md) - Component architecture and data flow
   - [low_latency.md](/.agent/system/architecture/low_latency.md) - Latency tuning and recommended settings

2. **REFER TO `.agent/sop/`** for procedures:
   - [local_setup.md](/.agent/sop/development/local_setup.md) - Full environment setup

**When in doubt, READ documentation first.**

---

## Code Generation Patterns

### Project Structure
- **Python 3.10+** with type hints (union syntax `X | None`)
- **faster-whisper** for Whisper inference (CTranslate2/CUDA backend)
- **sounddevice** for real-time audio capture (PortAudio/WASAPI)
- **Silero VAD** via torch.hub for voice activity detection

### File Layout
```
voice_dictation/
  ├── __main__.py       # CLI entry point, arg parsing, main loop
  ├── audio.py          # AudioCapture: mic → queue (background thread)
  ├── vad.py            # VADFilter: Silero VAD speech detection
  ├── transcriber.py    # TranscriptionEngine: faster-whisper GPU wrapper
  ├── processor.py      # StreamingProcessor: local agreement + buffer mgmt
  └── output.py         # ConsoleOutput / KeyboardOutput (Win32 SendInput)
```

### Key Patterns
- Audio capture runs in a sounddevice callback thread, feeds a bounded `queue.Queue`
- Main thread polls queue → VAD → processor → output (single-threaded pipeline)
- Streaming uses **local agreement**: text confirmed only when stable across 2 consecutive transcriptions
- Audio buffer is trimmed to 30s max to keep transcription fast
- All status/debug output goes to stderr; only transcription text goes to stdout
- `--keyboard` mode uses Win32 `SendInput` with Unicode scan codes

---

## Key Technologies

- **faster-whisper** >=1.1.0 - CTranslate2-based Whisper inference
- **sounddevice** >=0.5.0 - PortAudio wrapper for real-time audio
- **Silero VAD** - Voice activity detection via torch.hub
- **PyTorch** >=2.0 - CUDA 12.8 nightly for RTX 5090 (Blackwell sm_120)
- **numpy** >=1.24 - Audio array processing

---

## Important Notes

- **CUDA 12.8 nightly PyTorch is required** for RTX 5090 Blackwell architecture (sm_120)
- WASAPI is preferred on Windows for lowest audio capture latency
- Setting `--language` explicitly (e.g., `--language en`) skips auto-detection and reduces latency
- `beam_size=1` (greedy decoding) is default and critical for real-time performance
- For low-latency tuning details, see `.agent/system/architecture/low_latency.md`

---

For detailed documentation, refer to **`.agent/`**.
