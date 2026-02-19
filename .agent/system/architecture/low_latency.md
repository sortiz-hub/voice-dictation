# Low Latency Settings & Tuning Guide

This document covers recommended settings for minimizing end-to-end latency (speech → text on screen) and the trade-offs involved.

## 1. Latency Budget

| Stage | Typical Latency | Notes |
|-------|----------------|-------|
| Audio capture | ~5ms | WASAPI exclusive mode, 100ms blocks |
| VAD processing | ~1ms | Silero VAD is CPU-lightweight |
| Chunk accumulation | 0–1000ms | Waits for `chunk_size` interval |
| Whisper inference | 50–300ms | Depends on model + audio length + GPU |
| Local agreement | ~0ms | String comparison only |
| Output rendering | ~1ms | stdout write or SendInput |
| **Total (confirmed)** | **~100–500ms** | With optimal settings on RTX 5090 |
| **Total (partial)** | **~100–300ms** | Partial text appears faster |

The dominant factor is **chunk accumulation wait** + **Whisper inference time**. Tuning these two gives the biggest gains.

## 2. Recommended Settings by Use Case

### Lowest Latency (English, RTX 5090)
```bash
python -m voice_dictation \
  --model distil-large-v3 \
  --language en \
  --chunk-size 0.5 \
  --beam-size 1 \
  --compute-type float16 \
  --vad-threshold 0.4 \
  --min-silence-ms 400
```
- **distil-large-v3**: ~3x faster than large-v3, marginal accuracy loss for English
- **--language en**: Skips language detection on every chunk (saves ~50ms per inference)
- **--chunk-size 0.5**: Transcribe every 500ms instead of 1000ms
- **--vad-threshold 0.4**: Slightly more sensitive, catches speech onset faster
- **--min-silence-ms 400**: Finalizes utterances faster after pauses

### Balanced (Any Language, RTX 5090)
```bash
python -m voice_dictation \
  --model large-v3-turbo \
  --language <your-lang> \
  --chunk-size 0.8 \
  --beam-size 1 \
  --compute-type float16 \
  --min-silence-ms 600
```
- **large-v3-turbo**: Best accuracy/speed trade-off across languages
- Explicit language still recommended to avoid per-chunk detection overhead

### Maximum Accuracy (Slower)
```bash
python -m voice_dictation \
  --model large-v3 \
  --beam-size 5 \
  --chunk-size 2.0 \
  --compute-type float16
```
- **large-v3**: Highest accuracy model, but ~6x slower than turbo variant
- **beam-size 5**: Better decoding at cost of latency
- **chunk-size 2.0**: More audio context per transcription = better accuracy

## 3. Parameter Trade-offs

### Model Selection

| Model | Relative Speed | Accuracy | VRAM (float16) | Best For |
|-------|---------------|----------|----------------|----------|
| tiny | 30x | Low | ~1 GB | Testing only |
| base | 15x | Fair | ~1 GB | Testing only |
| small | 8x | Good | ~2 GB | Low-resource GPUs |
| medium | 4x | Good+ | ~3 GB | Mid-range GPUs |
| large-v2 | 1.5x | High | ~5 GB | Legacy compatibility |
| large-v3 | 1x | Highest | ~5 GB | Maximum accuracy |
| **large-v3-turbo** | **6x** | **High** | **~5 GB** | **Default — best balance** |
| **distil-large-v3** | **6-8x** | **High (EN)** | **~3 GB** | **Fastest for English** |

### chunk-size (seconds)

| Value | Effect |
|-------|--------|
| 0.3 | Very responsive but more GPU cycles, may waste compute on incomplete words |
| **0.5** | **Good for low-latency use cases** |
| **1.0** | **Default — balanced latency and efficiency** |
| 2.0+ | Higher accuracy per chunk but noticeable delay before text appears |

Lower values mean more frequent transcription calls. On RTX 5090, the GPU can handle chunk_size=0.5 easily even with large-v3-turbo.

### beam-size

| Value | Effect |
|-------|--------|
| **1** | **Greedy decoding — fastest, default for real-time** |
| 3 | Mild accuracy boost, ~2x slower |
| 5 | Best accuracy, ~3x slower |

Always use `beam_size=1` for real-time dictation. Only increase for batch/offline use.

### compute-type

| Type | Speed | Accuracy | Notes |
|------|-------|----------|-------|
| **float16** | **Fastest** | **Best** | **Default — uses Tensor Cores on RTX 5090** |
| int8_float16 | ~10% faster | Slightly lower | Mixed precision, marginal gain |
| int8 | ~15% faster | Lower | Full quantization, not recommended for dictation |

float16 is optimal for RTX 5090 — Tensor Cores are designed for FP16 workloads.

### vad-threshold

| Value | Effect |
|-------|--------|
| 0.3 | Very sensitive — catches quiet speech but may trigger on background noise |
| **0.4** | **Good for low-latency — catches speech onset quickly** |
| **0.5** | **Default — balanced** |
| 0.7 | Conservative — may miss soft-spoken beginnings |

### min-silence-ms

| Value | Effect |
|-------|--------|
| 300 | Aggressive — may split mid-sentence pauses |
| **400** | **Good for fast typists who want quick finalization** |
| **600** | **Default — handles natural dictation pauses** |
| 1000 | Very patient — good for slow/thoughtful speech |

### --language (explicit vs auto-detect)

Setting `--language` explicitly is one of the easiest latency wins:
- Auto-detect runs language identification on the first 30 seconds of each chunk
- Explicit language skips this entirely, saving ~30-80ms per transcription call
- Always set `--language` when you know the language you'll be speaking

## 4. Audio Device Selection

The application prefers **WASAPI** devices on Windows for lowest audio capture latency. When listing devices (`--list-devices`), non-WASAPI devices are filtered out if WASAPI is available.

For absolute lowest latency:
- Use a USB microphone (avoids analog path latency)
- Ensure WASAPI is the active host API (default on modern Windows)
- The 100ms block size is a good default — smaller blocks increase CPU overhead without meaningful latency improvement since the bottleneck is Whisper inference

## 5. Warmup

The application runs a warmup transcription (1s of silence) at startup. This ensures:
- CUDA kernels are compiled/cached
- Model weights are loaded into GPU memory
- First real transcription runs at full speed

First-run after install may be slower due to CUDA kernel JIT compilation. Subsequent runs benefit from the CUDA cache.

## 6. Memory Management

- Audio buffer is capped at **30 seconds** (`max_samples = 30 * sample_rate`)
- When exceeded, oldest audio is trimmed from the buffer
- This prevents unbounded VRAM growth during long utterances
- For very long continuous speech, confirmed text is committed and the sliding window provides context
