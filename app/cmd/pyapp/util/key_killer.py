import sys

try:
    import msvcrt
except Exception:
    pass
import ctypes

kernel32 = None

if "msvcrt" in globals():
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

ENABLE_ECHO_INPUT = 0x0004


def isWindows():
    return kernel32 is not None


def _check_bool(result, func, args):
    if not result:
        raise ctypes.WinError(ctypes.get_last_error())
    return args


if kernel32 is not None:
    kernel32.GetConsoleMode.errcheck = _check_bool
    kernel32.GetConsoleMode.argtypes = (ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong))
    kernel32.SetConsoleMode.errcheck = _check_bool
    kernel32.SetConsoleMode.argtypes = (ctypes.c_void_p, ctypes.c_ulong)
    kernel32.FlushConsoleInputBuffer.errcheck = _check_bool
    kernel32.FlushConsoleInputBuffer.argtypes = (ctypes.c_void_p,)


def echo_input(enable=True, conin=sys.stdin):
    if "msvcrt" not in globals():
        return

    h = msvcrt.get_osfhandle(conin.fileno())
    try:
        mode = ctypes.c_ulong()
        kernel32.GetConsoleMode(h, ctypes.byref(mode))
        if enable:
            mode.value |= ENABLE_ECHO_INPUT
        else:
            mode.value &= ~ENABLE_ECHO_INPUT
        kernel32.SetConsoleMode(h, mode)
    except Exception:
        pass


def flush_input(conin=sys.stdin):
    if "msvcrt" not in globals():
        return

    h = msvcrt.get_osfhandle(conin.fileno())
    kernel32.FlushConsoleInputBuffer(h)


if __name__ == "__main__":
    import time

    echo_input(False)

    for i in range(10):
        print(i)
        time.sleep(1)

    echo_input(True)
    flush_input()

    print(input("Answer now: "))
