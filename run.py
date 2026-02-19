"""Entry point wrapper for PyInstaller — enables relative imports in voice_dictation package."""

from voice_dictation.__main__ import main

if __name__ == "__main__":
    main()
