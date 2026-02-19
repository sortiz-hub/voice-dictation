"""Build script for voice-dictation Windows binary."""

import os
import shutil
import subprocess
import sys


def main():
    root = os.path.dirname(os.path.abspath(__file__))
    dist_dir = os.path.join(root, "dist", "voice-dictation")
    spec_file = os.path.join(root, "voice_dictation.spec")

    # Clean previous builds
    for d in ["build", "dist"]:
        path = os.path.join(root, d)
        if os.path.exists(path):
            print(f"Cleaning {path}...")
            shutil.rmtree(path)

    # Run PyInstaller
    print("\n=== Running PyInstaller ===\n")
    result = subprocess.run(
        [sys.executable, "-m", "PyInstaller", "--noconfirm", spec_file],
        cwd=root,
    )
    if result.returncode != 0:
        print(f"\nERROR: PyInstaller failed with exit code {result.returncode}")
        sys.exit(1)

    # Verify critical files
    # PyInstaller 6.x puts data/binaries under _internal/
    internal = os.path.join(dist_dir, "_internal")
    print("\n=== Verifying output ===\n")
    checks = {
        "voice-dictation.exe": (dist_dir, "voice-dictation.exe"),
        "silero_vad_v6.onnx": (internal, os.path.join("faster_whisper", "assets", "silero_vad_v6.onnx")),
        "libportaudio64bit.dll": (internal, os.path.join("_sounddevice_data", "portaudio-binaries", "libportaudio64bit.dll")),
        "ctranslate2.dll": (internal, os.path.join("ctranslate2", "ctranslate2.dll")),
    }

    # Also check for any torch CUDA DLL
    torch_cuda_found = False
    for dirpath, _, filenames in os.walk(dist_dir):
        for f in filenames:
            if "torch_cuda" in f.lower() or "cudnn" in f.lower() or "cublas" in f.lower():
                torch_cuda_found = True
                break
        if torch_cuda_found:
            break

    all_ok = True
    for label, (base, rel_path) in checks.items():
        full = os.path.join(base, rel_path)
        if os.path.exists(full):
            size_mb = os.path.getsize(full) / (1024 * 1024)
            print(f"  OK  {label} ({size_mb:.1f} MB)")
        else:
            print(f"  MISSING  {label}  (expected at {rel_path})")
            all_ok = False

    if torch_cuda_found:
        print("  OK  torch CUDA DLLs found")
    else:
        print("  WARN  No torch CUDA DLLs found (may still work if torch handles this)")

    # Total size
    total = 0
    for dirpath, _, filenames in os.walk(dist_dir):
        for f in filenames:
            total += os.path.getsize(os.path.join(dirpath, f))
    total_gb = total / (1024 ** 3)
    print(f"\nTotal distribution size: {total_gb:.2f} GB")

    if all_ok:
        print(f"\nBuild complete: {dist_dir}")
        print("\nTest with:")
        print(f'  "{os.path.join(dist_dir, "voice-dictation.exe")}" --list-devices')
    else:
        print("\nBuild completed with missing files — check errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
