# Local Development Setup

## Prerequisites

| Requirement | Version | How to Check |
|-------------|---------|--------------|
| Windows 11 | 10.0+ | `winver` |
| Python | 3.10+ | `python --version` |
| NVIDIA GPU | RTX 5090 (or any CUDA 12 GPU) | `nvidia-smi` |
| NVIDIA Driver | Latest (CUDA 12.x support) | `nvidia-smi` (top line) |
| CUDA Toolkit | 12.x | `nvcc --version` |
| Microphone | Any input device | Windows Sound Settings |

## Setup Steps

### 1. Clone Repository

```bash
git clone https://github.com/sortiz-hub/voice-dictation.git
cd voice-dictation
```

### 2. Create Virtual Environment

```bash
python -m venv .venv
.venv/Scripts/activate
```

### 3. Install PyTorch with CUDA 12.8

**This step is critical.** The RTX 5090 (Blackwell, sm_120) requires CUDA 12.8 nightly builds.

```bash
pip install --pre torch torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128
```

Verify CUDA is working:
```bash
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

Expected output: `True NVIDIA GeForce RTX 5090`

### 4. Install Project

```bash
pip install -e .
```

This installs faster-whisper, sounddevice, and numpy.

### 5. Verify Installation

```bash
# List audio devices
python -m voice_dictation --list-devices

# Console test mode (prints to stdout)
python -m voice_dictation --console

# Default keyboard mode (types into focused window)
python -m voice_dictation
```

On first run, the Whisper model will be downloaded (~1 GB for distil-large-v3). Subsequent runs use the cached model.

### 6. Build Binary (Optional)

```bash
pip install pyinstaller
python build.py
```

See [packaging.md](../deployment/packaging.md) for details.

## Troubleshooting

### "No CUDA GPU detected"
- Run `nvidia-smi` to check driver status
- Verify PyTorch was installed with CUDA: `python -c "import torch; print(torch.version.cuda)"`
- If it shows `None`, reinstall PyTorch with the CUDA index URL

### "No audio input devices found"
- Check Windows Sound Settings → Input devices
- Ensure microphone is connected and enabled
- Try specifying a device index: `python -m voice_dictation --device 0`

### Model download fails
- faster-whisper downloads from Hugging Face on first use
- Check internet connection for initial download
- Models are cached in `~/.cache/huggingface/` — no internet needed after first download

### Slow first transcription
- CUDA kernels are JIT-compiled on first run — this is normal
- The warmup step at startup mitigates this
- Subsequent runs are faster due to CUDA cache

### "torch not found" or CUDA version mismatch
- Ensure you installed from the nightly cu128 index, not the default PyPI torch
- `pip uninstall torch torchaudio` then reinstall with the correct index URL
