"""Entry point for voice dictation."""

import argparse
import signal
import sys
import time

import numpy as np


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="voice-dictation",
        description="Real-time voice dictation using local Whisper models on GPU.",
    )
    p.add_argument("--model", default="large-v3-turbo",
                   choices=["tiny", "base", "small", "medium", "large-v2", "large-v3", "large-v3-turbo", "distil-large-v3"],
                   help="Whisper model (default: large-v3-turbo)")
    p.add_argument("--language", default=None,
                   help="Language code, e.g. en, es, de (default: auto-detect)")
    p.add_argument("--device", type=int, default=None,
                   help="Audio input device index (see --list-devices)")
    p.add_argument("--list-devices", action="store_true",
                   help="List available audio input devices and exit")
    p.add_argument("--chunk-size", type=float, default=1.0,
                   help="Min audio chunk in seconds (default: 1.0)")
    p.add_argument("--beam-size", type=int, default=1,
                   help="Beam size for decoding (default: 1)")
    p.add_argument("--compute-type", default="float16",
                   choices=["float16", "int8_float16", "int8"],
                   help="Compute type (default: float16)")
    p.add_argument("--vad-threshold", type=float, default=0.5,
                   help="VAD speech probability threshold (default: 0.5)")
    p.add_argument("--min-silence-ms", type=int, default=600,
                   help="Min silence duration to end speech segment in ms (default: 600)")
    p.add_argument("--keyboard", action="store_true",
                   help="Type transcription as keystrokes into the focused window")
    p.add_argument("--keyboard-delay", type=float, default=0.0,
                   help="Delay between keystrokes in seconds (default: 0.0)")
    return p.parse_args()


def log(msg: str):
    """Always print status to stderr so it shows even in --keyboard mode."""
    print(msg, file=sys.stderr, flush=True)


def print_banner(args, gpu_name: str, device_name: str):
    log("")
    log("=" * 52)
    log("  Voice Dictation v0.1")
    log(f"  Model:    {args.model} ({args.compute_type})")
    log(f"  GPU:      {gpu_name}")
    log(f"  Language: {args.language or 'auto-detect'}")
    log(f"  Device:   {device_name}")
    if args.keyboard:
        log("  Output:   KEYBOARD (Alt+Tab to target window)")
    log("=" * 52)
    log("")


def get_gpu_name() -> str:
    try:
        import torch
        if torch.cuda.is_available():
            return torch.cuda.get_device_name(0)
        return "No CUDA GPU"
    except Exception:
        return "Unknown"


def main():
    args = parse_args()

    # --list-devices
    if args.list_devices:
        from .audio import AudioCapture
        devices = AudioCapture.list_devices()
        if not devices:
            print("No audio input devices found.")
            sys.exit(1)
        print("\nAvailable input devices:")
        for d in devices:
            default_marker = "  *default*" if d["default"] else ""
            print(f"  [{d['index']}] {d['name']}{default_marker}")
        print(f"\nUse --device <number> to select.")
        sys.exit(0)

    # Check CUDA
    try:
        import torch
        if not torch.cuda.is_available():
            print("ERROR: No CUDA GPU detected.", file=sys.stderr)
            print("  This application requires an NVIDIA GPU with CUDA 12 support.", file=sys.stderr)
            print("  Check your drivers: nvidia-smi", file=sys.stderr)
            sys.exit(1)
    except ImportError:
        print("ERROR: PyTorch not installed. Install with: pip install torch", file=sys.stderr)
        sys.exit(1)

    # Load components
    from .audio import AudioCapture
    from .vad import VADFilter
    from .transcriber import TranscriptionEngine
    from .processor import StreamingProcessor
    from .output import ConsoleOutput

    gpu_name = get_gpu_name()

    engine = TranscriptionEngine(
        model_name=args.model,
        compute_type=args.compute_type,
        language=args.language,
        beam_size=args.beam_size,
    )

    log("Warming up...")
    engine.warmup()
    log("Warming up... done.")

    log("Loading VAD...")
    vad = VADFilter(
        threshold=args.vad_threshold,
    )
    log("Loading VAD... done.")

    processor = StreamingProcessor(engine, chunk_size=args.chunk_size)

    if args.keyboard:
        from .output import KeyboardOutput
        output = KeyboardOutput(delay=args.keyboard_delay)
    else:
        output = ConsoleOutput()

    audio = AudioCapture(device=args.device)
    devices = audio.list_devices()
    device_name = "Unknown"
    if args.device is not None:
        for d in devices:
            if d["index"] == args.device:
                device_name = d["name"]
                break
    else:
        for d in devices:
            if d["default"]:
                device_name = d["name"]
                break

    print_banner(args, gpu_name, device_name)
    log("Listening. Speak now. (Ctrl+C to stop)")
    if args.keyboard:
        log(">>> Alt+Tab to your target window now <<<")
    log("")

    # Graceful shutdown
    shutdown = False

    def on_sigint(sig, frame):
        nonlocal shutdown
        shutdown = True

    signal.signal(signal.SIGINT, on_sigint)

    audio.start()

    speaking = False
    silence_chunks = 0
    # Audio chunks are ~100ms each.
    # Short silence: keep accumulating audio (natural pauses between words)
    # Long silence: finalize the utterance
    # Use a generous threshold — natural speech has 300-500ms pauses between phrases.
    # Only finalize after sustained silence (min_silence_ms, default 600ms = 6 chunks).
    silence_limit = max(3, args.min_silence_ms // 100)

    try:
        while not shutdown:
            chunk = audio.get_audio(timeout=0.1)
            if chunk is None:
                continue

            has_speech = vad.is_speech(chunk)

            if has_speech:
                if not speaking:
                    speaking = True
                    log("[listening...]")

                silence_chunks = 0

                # Feed audio to processor — transcribes periodically
                confirmed, partial = processor.feed_audio(chunk)

                if confirmed:
                    output.print_confirmed(confirmed)
                    log(f"[confirmed] {confirmed.strip()}")
                if partial and not args.keyboard:
                    output.print_partial(partial)

            elif speaking:
                # Brief silence while in a speech session — KEEP feeding audio.
                # This is critical: natural speech has pauses between words/phrases.
                # We keep accumulating so Whisper sees the full context.
                confirmed, partial = processor.feed_audio(chunk)

                if confirmed:
                    output.print_confirmed(confirmed)
                    log(f"[confirmed] {confirmed.strip()}")
                if partial and not args.keyboard:
                    output.print_partial(partial)

                silence_chunks += 1

                if silence_chunks >= silence_limit:
                    # Long silence — finalize this utterance
                    remaining = processor.finish()
                    if remaining:
                        output.print_confirmed(remaining)
                        log(f"[flushed] {remaining.strip()}")
                    output.print_confirmed(" ")
                    speaking = False
                    silence_chunks = 0
                    vad.reset()
                    log("[end of utterance]")

    except Exception as e:
        log(f"\nError: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
    finally:
        audio.stop()
        remaining = processor.finish()
        if remaining:
            output.print_confirmed(remaining)
        output.commit_line()
        log("\n--- Dictation ended. ---")


if __name__ == "__main__":
    main()
