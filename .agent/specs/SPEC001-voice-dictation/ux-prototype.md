# SPEC001 - UX Prototype: Console Interface

## 1. Startup Sequence

```
$ python -m voice_dictation --model large-v3-turbo --language en

╔══════════════════════════════════════════════════╗
║  Voice Dictation v0.1                            ║
║  Model:    large-v3-turbo (float16)              ║
║  GPU:      NVIDIA RTX 5090 (32 GB)               ║
║  Language: English                                ║
║  Device:   Microphone Array (Realtek)             ║
╚══════════════════════════════════════════════════╝

Loading model... ████████████████████████████ 100%
Warming up engine... done (0.3s)

Listening. Speak now. (Ctrl+C to stop)

```

## 2. Active Dictation

Confirmed text prints on committed lines. Partial text overwrites in-place on the current line.

```
The quick brown fox jumps over the lazy dog.
She sells seashells by the seashore.
The weather today is particularly_ ← partial (blinking cursor, overwritten in-place)
```

When the partial text is confirmed:

```
The quick brown fox jumps over the lazy dog.
She sells seashells by the seashore.
The weather today is particularly nice for a walk in the park.
I think we should_ ← new partial
```

## 3. Silence / Pauses

During silence, no phantom text appears. The cursor stays on the partial line:

```
The quick brown fox jumps over the lazy dog.
█  ← cursor sits idle, no output during silence
```

## 4. Shutdown (Ctrl+C)

```
The quick brown fox jumps over the lazy dog.
She sells seashells by the seashore.
The weather today is particularly nice.

--- Dictation ended. Flushed remaining buffer. ---
```

## 5. Device Listing

```
$ python -m voice_dictation --list-devices

Available input devices:
  [0] Microphone Array (Realtek)  *default*
  [1] USB Condenser Mic (Blue Yeti)
  [2] Stereo Mix (Realtek)

Use --device <number> to select.
```

## 6. Error States

### No GPU
```
ERROR: No CUDA GPU detected.
  This application requires an NVIDIA GPU with CUDA 12 support.
  Check your drivers: nvidia-smi
```

### No Microphone
```
ERROR: No audio input device found.
  Connect a microphone and try again.
  Available devices: (none)
```

### Model Not Downloaded
```
Model 'large-v3-turbo' not found in cache.
Downloading from Hugging Face Hub... ████████░░░░░░░░ 52%
```

## 7. Help Output

```
$ python -m voice_dictation --help

usage: voice_dictation [-h] [--model MODEL] [--language LANG]
                       [--device ID] [--list-devices]
                       [--chunk-size SEC] [--beam-size N]
                       [--compute-type TYPE]

Real-time voice dictation using local Whisper models on GPU.

options:
  --model MODEL        Whisper model (default: large-v3-turbo)
                       Choices: tiny, base, small, medium, large-v2,
                       large-v3, large-v3-turbo, distil-large-v3
  --language LANG      Language code, e.g. en, es, de (default: auto)
  --device ID          Audio input device index (see --list-devices)
  --list-devices       List available audio input devices and exit
  --chunk-size SEC     Min audio chunk in seconds (default: 1.0)
  --beam-size N        Beam size for decoding (default: 1)
  --compute-type TYPE  float16, int8_float16, int8 (default: float16)
  -h, --help           Show this help message
```

## 8. Interaction Summary

| User Action | System Response |
|-------------|-----------------|
| Launch app | Load model, show banner, start listening |
| Speak | Partial text appears immediately, confirmed text commits to new line |
| Pause/Silence | No output, cursor idles |
| Resume speaking | New partial text appears |
| Ctrl+C | Flush buffer, print final text, clean exit |
| --list-devices | Print device list, exit |
| No GPU / No mic | Print specific error, exit with code 1 |
