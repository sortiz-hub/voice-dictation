# Packaging: Windows Binary

## Overview

The application is packaged as a standalone Windows `.exe` using PyInstaller in one-directory mode. The output is a `dist/voice-dictation/` folder (~4.3 GB) containing the exe and all dependencies. No Python installation required on the target machine — only an NVIDIA GPU with CUDA-capable drivers.

## Prerequisites

| Requirement | Notes |
|-------------|-------|
| Working dev environment | See [local_setup.md](../development/local_setup.md) |
| PyInstaller | `pip install pyinstaller` |
| All runtime deps installed | faster-whisper, torch, sounddevice, etc. |

## Build

```bash
pip install pyinstaller
python build.py
```

The build script:
1. Cleans `build/` and `dist/` directories
2. Runs PyInstaller with `voice_dictation.spec`
3. Verifies critical files exist in output
4. Reports total distribution size

## Output Structure

```
dist/voice-dictation/
├── voice-dictation.exe              # Main executable
└── _internal/
    ├── faster_whisper/assets/
    │   └── silero_vad_v6.onnx       # VAD model (bundled)
    ├── _sounddevice_data/
    │   └── portaudio-binaries/
    │       └── libportaudio64bit.dll # Audio capture
    ├── ctranslate2/
    │   └── ctranslate2.dll          # Whisper inference backend
    ├── torch/lib/
    │   └── *.dll                    # CUDA, cuDNN, cublas (~4 GB)
    └── ...                          # Python stdlib, other deps
```

## Verification

After building, test outside the venv:

```bash
# List audio devices (validates sounddevice + PortAudio)
dist\voice-dictation\voice-dictation.exe --list-devices

# Console test mode (validates CUDA, model download, VAD, transcription)
dist\voice-dictation\voice-dictation.exe --console

# Keyboard mode (validates Win32 SendInput)
dist\voice-dictation\voice-dictation.exe
```

On first run, the Whisper model downloads from Hugging Face (~1-3 GB depending on model). Subsequent runs use the cached model from `~/.cache/huggingface/`.

## Architecture Decisions

| Decision | Rationale |
|----------|-----------|
| **onedir** (not onefile) | Avoids slow self-extraction of multi-GB archive on every launch |
| **UPX disabled** | UPX corrupts CUDA/cuDNN DLLs |
| **ONNX VAD** (not torch.hub) | `torch.hub.load()` requires Git at runtime, which breaks in frozen builds |
| **Models not bundled** | Whisper models are 1-3 GB each; download on first run keeps the binary manageable |
| **`run.py` wrapper** | PyInstaller needs a top-level script; relative imports in `__main__.py` fail without a package context |
| **Custom ctranslate2 hook** | PyInstaller's built-in hooks don't collect ctranslate2's DLLs |
| **Runtime hook for faster_whisper** | `get_assets_path()` uses `__file__` which resolves differently in frozen builds |

## Key Files

| File | Purpose |
|------|---------|
| `voice_dictation.spec` | PyInstaller spec — defines binaries, data, hidden imports, exclusions |
| `build.py` | Build + verification script |
| `run.py` | Entry point wrapper for frozen builds |
| `hooks/hook-ctranslate2.py` | Collects ctranslate2 `.dll` and `.pyd` files |
| `hooks/pyi_rth_faster_whisper.py` | Patches `get_assets_path()` to use `sys._MEIPASS` |

## Troubleshooting

### "Failed to execute script"
- Usually a missing hidden import. Check `build/voice_dictation/warn-voice_dictation.txt` for import warnings.
- Add missing modules to `hiddenimports` in the spec file.

### Missing DLLs at runtime
- Check `dist/voice-dictation/_internal/` for the expected DLL.
- If missing, add it to `binaries` in the spec file or create a custom hook.

### CUDA errors in packaged binary
- Ensure the target machine has compatible NVIDIA drivers (CUDA 12.x).
- The binary bundles CUDA runtime DLLs but still requires a compatible driver.

### Model download fails
- The binary needs internet access on first run to download from Hugging Face.
- Models are cached in `%USERPROFILE%\.cache\huggingface\`.
