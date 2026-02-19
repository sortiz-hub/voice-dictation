# Voice Dictation Documentation

Welcome to the Voice Dictation documentation! This folder contains comprehensive documentation to help engineers understand and work with the system.

## Documentation Structure

```
.agent/
├── README.md                           # This file — documentation index
├── system/
│   └── architecture/
│       ├── overview.md                 # Component architecture, data flow, threading, packaging
│       └── low_latency.md             # Latency tuning, recommended settings per use case
├── sop/
│   ├── development/
│   │   └── local_setup.md             # Full environment setup (CUDA, PyTorch, project)
│   └── deployment/
│       └── packaging.md               # Building the Windows binary with PyInstaller
└── specs/                             # Feature specifications (managed by spec-writer)
```

## Quick Start

### For New Engineers
1. **Start here**: [system/architecture/overview.md](system/architecture/overview.md)
2. **Set up environment**: [sop/development/local_setup.md](sop/development/local_setup.md)
3. **Tune for latency**: [system/architecture/low_latency.md](system/architecture/low_latency.md)

### For Building the Binary
1. **Set up environment**: [sop/development/local_setup.md](sop/development/local_setup.md)
2. **Build and verify**: [sop/deployment/packaging.md](sop/deployment/packaging.md)

### For Feature Development
1. Investigate [specs/](specs/) folder for available feature specifications
2. Review [system/architecture/overview.md](system/architecture/overview.md) for component architecture
3. Follow [sop/development/local_setup.md](sop/development/local_setup.md) for environment setup

### For Debugging
1. Check [system/architecture/overview.md](system/architecture/overview.md) for component details and data flow
2. Review [system/architecture/low_latency.md](system/architecture/low_latency.md) for performance bottleneck analysis

---

## System Documentation

| Document | Description | Key Topics |
|----------|-------------|------------|
| [overview.md](system/architecture/overview.md) | Complete system architecture | Components, data flow, threading, packaging, ONNX VAD |
| [low_latency.md](system/architecture/low_latency.md) | Latency tuning guide | Default settings, parameter trade-offs, use case profiles |

---

## SOPs (Standard Operating Procedures)

| SOP | Description | When to Use |
|-----|-------------|-------------|
| [local_setup.md](sop/development/local_setup.md) | Environment setup | Setting up dev environment from scratch |
| [packaging.md](sop/deployment/packaging.md) | Windows binary build | Packaging the app as a standalone .exe |

---

## Specifications

Feature specifications are maintained in the `specs/` folder. Specs change frequently, so this index intentionally does not list them. When working on features, investigate the `specs/` folder directly to discover available specifications.

---

## Quick Reference

### Common Commands
```bash
# Run with defaults (keyboard mode, low-latency English)
python -m voice_dictation

# Console test mode (prints to stdout)
python -m voice_dictation --console

# List audio devices
python -m voice_dictation --list-devices

# Different model/language
python -m voice_dictation --model large-v3-turbo --language es

# Build standalone binary
pip install pyinstaller && python build.py

# Run packaged binary
dist\voice-dictation\voice-dictation.exe
dist\voice-dictation\voice-dictation.exe --console
```

### Key CLI Flags
| Flag | Default | Description |
|------|---------|-------------|
| `--model` | distil-large-v3 | Whisper model variant |
| `--language` | en | Language code (e.g., en, es, de) |
| `--device` | system default | Audio input device index |
| `--chunk-size` | 0.5 | Min seconds between transcriptions |
| `--beam-size` | 1 | Beam search width (1 = greedy) |
| `--compute-type` | float16 | Model precision (float16, int8_float16, int8) |
| `--vad-threshold` | 0.4 | Speech probability threshold |
| `--min-silence-ms` | 400 | Silence duration to end utterance (ms) |
| `--console` | off | Console test mode (stdout instead of keystrokes) |
| `--keyboard-delay` | 0.0 | Delay between keystrokes (seconds) |
