# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for voice-dictation (onedir, console, CUDA)."""

import os
import sys
import site

block_cipher = None

# --- Locate site-packages ---
sp = None
for p in site.getsitepackages():
    if os.path.isdir(os.path.join(p, "faster_whisper")):
        sp = p
        break
if sp is None:
    sp = os.path.join(sys.prefix, "Lib", "site-packages")

# --- Data files ---
datas = [
    # Silero VAD ONNX model
    (os.path.join(sp, "faster_whisper", "assets", "silero_vad_v6.onnx"),
     os.path.join("faster_whisper", "assets")),
    # PortAudio DLL
    (os.path.join(sp, "_sounddevice_data", "portaudio-binaries", "libportaudio64bit.dll"),
     os.path.join("_sounddevice_data", "portaudio-binaries")),
    # certifi CA bundle
    (os.path.join(sp, "certifi", "cacert.pem"),
     "certifi"),
]

# --- Binaries ---
binaries = []

# ctranslate2 DLLs
ct2_dir = os.path.join(sp, "ctranslate2")
if os.path.isdir(ct2_dir):
    for f in os.listdir(ct2_dir):
        if f.endswith((".dll", ".pyd")):
            binaries.append((os.path.join(ct2_dir, f), "ctranslate2"))

# onnxruntime DLLs
ort_capi = os.path.join(sp, "onnxruntime", "capi")
if os.path.isdir(ort_capi):
    for f in os.listdir(ort_capi):
        if f.endswith((".dll", ".pyd")):
            binaries.append((os.path.join(ort_capi, f), os.path.join("onnxruntime", "capi")))

# --- Analysis ---
a = Analysis(
    ["run.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=[
        "voice_dictation",
        "voice_dictation.audio",
        "voice_dictation.vad",
        "voice_dictation.transcriber",
        "voice_dictation.processor",
        "voice_dictation.output",
        "torch",
        "ctranslate2",
        "onnxruntime",
        "sounddevice",
        "huggingface_hub",
        "certifi",
        "numpy",
        "faster_whisper",
    ],
    hookspath=["hooks"],
    hooksconfig={},
    runtime_hooks=["hooks/pyi_rth_faster_whisper.py"],
    excludes=[
        "matplotlib",
        "tkinter",
        "PIL",
        "IPython",
        "jupyter",
        "pytest",
        "setuptools",
        "pip",
        "wheel",
    ],
    noarchive=False,
    optimize=0,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="voice-dictation",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="voice-dictation",
)
