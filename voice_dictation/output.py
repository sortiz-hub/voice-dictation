"""Output rendering — console or keyboard simulation."""

import sys


class ConsoleOutput:
    def __init__(self):
        self._partial_len = 0

    def print_confirmed(self, text: str) -> None:
        if not text:
            return
        self._clear_partial()
        sys.stdout.write(text)
        sys.stdout.flush()

    def print_partial(self, text: str) -> None:
        self._clear_partial()
        if text:
            sys.stdout.write(text)
            sys.stdout.flush()
            self._partial_len = len(text)

    def commit_line(self) -> None:
        self._clear_partial()
        sys.stdout.write("\n")
        sys.stdout.flush()

    def _clear_partial(self):
        if self._partial_len > 0:
            sys.stdout.write("\r" + " " * (self._partial_len + 80) + "\r")
            self._partial_len = 0


class KeyboardOutput:
    """Types text as keystrokes into the focused window using Win32 SendInput."""

    def __init__(self, delay: float = 0.0):
        import ctypes
        import ctypes.wintypes as w

        # Correct struct definitions for 64-bit Windows
        class MOUSEINPUT(ctypes.Structure):
            _fields_ = [
                ("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
            ]

        class KEYBDINPUT(ctypes.Structure):
            _fields_ = [
                ("wVk", w.WORD),
                ("wScan", w.WORD),
                ("dwFlags", w.DWORD),
                ("time", w.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
            ]

        class HARDWAREINPUT(ctypes.Structure):
            _fields_ = [
                ("uMsg", w.DWORD),
                ("wParamL", w.WORD),
                ("wParamH", w.WORD),
            ]

        class _INPUT_UNION(ctypes.Union):
            _fields_ = [
                ("mi", MOUSEINPUT),
                ("ki", KEYBDINPUT),
                ("hi", HARDWAREINPUT),
            ]

        class INPUT(ctypes.Structure):
            _fields_ = [
                ("type", w.DWORD),
                ("_input", _INPUT_UNION),
            ]

        self._INPUT = INPUT
        self._KEYBDINPUT = KEYBDINPUT
        self._INPUT_UNION = _INPUT_UNION
        self._ctypes = ctypes
        self._delay = delay
        self._partial_chars = 0

        self._SendInput = ctypes.windll.user32.SendInput
        self._SendInput.argtypes = [w.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
        self._SendInput.restype = w.UINT

        # Test it works
        count = self._send_test()
        print(f"[KeyboardOutput] SendInput test: {count} events sent", file=sys.stderr, flush=True)

    def _make_key_input(self, wVk=0, wScan=0, dwFlags=0):
        ctypes = self._ctypes
        inp = self._INPUT()
        inp.type = 1  # INPUT_KEYBOARD
        inp._input.ki.wVk = wVk
        inp._input.ki.wScan = wScan
        inp._input.ki.dwFlags = dwFlags
        inp._input.ki.time = 0
        inp._input.ki.dwExtraInfo = ctypes.pointer(ctypes.c_ulong(0))
        return inp

    def _send_test(self) -> int:
        """Send a harmless shift key press/release to test SendInput works."""
        KEYEVENTF_KEYUP = 0x0002
        VK_SHIFT = 0x10
        inputs = (self._INPUT * 2)()
        inputs[0] = self._make_key_input(wVk=VK_SHIFT)
        inputs[1] = self._make_key_input(wVk=VK_SHIFT, dwFlags=KEYEVENTF_KEYUP)
        return self._SendInput(2, inputs, self._ctypes.sizeof(self._INPUT))

    def _type_text(self, text: str):
        import time
        KEYEVENTF_UNICODE = 0x0004
        KEYEVENTF_KEYUP = 0x0002

        for char in text:
            code = ord(char)
            inputs = (self._INPUT * 2)()
            inputs[0] = self._make_key_input(wScan=code, dwFlags=KEYEVENTF_UNICODE)
            inputs[1] = self._make_key_input(wScan=code, dwFlags=KEYEVENTF_UNICODE | KEYEVENTF_KEYUP)
            sent = self._SendInput(2, inputs, self._ctypes.sizeof(self._INPUT))
            if sent == 0:
                err = self._ctypes.get_last_error()
                print(f"[KeyboardOutput] SendInput failed: error {err}", file=sys.stderr, flush=True)
            if self._delay > 0:
                time.sleep(self._delay)

    def _send_backspaces(self, count: int):
        KEYEVENTF_KEYUP = 0x0002
        VK_BACK = 0x08
        for _ in range(count):
            inputs = (self._INPUT * 2)()
            inputs[0] = self._make_key_input(wVk=VK_BACK)
            inputs[1] = self._make_key_input(wVk=VK_BACK, dwFlags=KEYEVENTF_KEYUP)
            self._SendInput(2, inputs, self._ctypes.sizeof(self._INPUT))

    def print_confirmed(self, text: str) -> None:
        if not text:
            return
        if self._partial_chars > 0:
            self._send_backspaces(self._partial_chars)
            self._partial_chars = 0
        self._type_text(text)

    def print_partial(self, text: str) -> None:
        if self._partial_chars > 0:
            self._send_backspaces(self._partial_chars)
            self._partial_chars = 0
        if text:
            self._type_text(text)
            self._partial_chars = len(text)

    def commit_line(self) -> None:
        if self._partial_chars > 0:
            self._send_backspaces(self._partial_chars)
            self._partial_chars = 0
