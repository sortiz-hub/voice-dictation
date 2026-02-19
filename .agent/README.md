# Voice Dictation Documentation

Welcome to the Voice Dictation documentation! This folder contains comprehensive documentation to help engineers understand and work with the system.

## Documentation Structure

```
.agent/
├── README.md                           # This file — documentation index
├── system/
│   └── architecture/
│       ├── overview.md                 # Component architecture, data flow, threading
│       └── low_latency.md             # Latency tuning, recommended settings per use case
├── sop/
│   └── development/
│       └── local_setup.md             # Full environment setup (CUDA, PyTorch, project)
└── specs/                             # Feature specifications (managed by spec-writer)
```

## Quick Start

### For New Engineers
1. **Start here**: [system/architecture/overview.md](system/architecture/overview.md)
2. **Set up environment**: [sop/development/local_setup.md](sop/development/local_setup.md)
3. **Tune for latency**: [system/architecture/low_latency.md](system/architecture/low_latency.md)

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
| [overview.md](system/architecture/overview.md) | Complete system architecture | Components, data flow, threading model, streaming strategy |
| [low_latency.md](system/architecture/low_latency.md) | Latency tuning guide | Recommended settings, parameter trade-offs, benchmarks |

---

## SOPs (Standard Operating Procedures)

| SOP | Description | When to Use |
|-----|-------------|-------------|
| [local_setup.md](sop/development/local_setup.md) | Environment setup | Setting up dev environment from scratch |

---

## Specifications

Feature specifications are maintained in the `specs/` folder. Specs change frequently, so this index intentionally does not list them. When working on features, investigate the `specs/` folder directly to discover available specifications.

---

## Quick Reference

### Common Commands
```bash
# Run with defaults
python -m voice_dictation

# Keyboard mode (types into focused window)
python -m voice_dictation --keyboard

# List audio devices
python -m voice_dictation --list-devices

# Fastest English-only
python -m voice_dictation --model distil-large-v3 --language en --chunk-size 0.5
```

### Key CLI Flags
| Flag | Default | Description |
|------|---------|-------------|
| `--model` | large-v3-turbo | Whisper model variant |
| `--language` | auto-detect | Language code (e.g., en, es, de) |
| `--device` | system default | Audio input device index |
| `--chunk-size` | 1.0 | Min seconds between transcriptions |
| `--beam-size` | 1 | Beam search width (1 = greedy) |
| `--compute-type` | float16 | Model precision (float16, int8_float16, int8) |
| `--vad-threshold` | 0.5 | Speech probability threshold |
| `--min-silence-ms` | 600 | Silence duration to end utterance (ms) |
| `--keyboard` | off | Type as keystrokes into focused window |
| `--keyboard-delay` | 0.0 | Delay between keystrokes (seconds) |
