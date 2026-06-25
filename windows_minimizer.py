import ctypes
import time
from WinToastCreator.creator import toast 
from ctypes import wintypes
print("Введите часы: ")
h = int(input())
print("Введите минуты: ")
m = int(input())
print("Введите секунды: ")
s = int(input())
d = h * 3600 + m * 60 + s
print("Введите заголовок сообщения: ")
title = input()
print("Введите текст сообщения: ")
text = input()
time.sleep(d)
user32 = ctypes.windll.user32
EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
SW_MINIMIZE = 6
@EnumWindowsProc
def enum_proc(hwnd, lparam):
    if not user32.IsWindowVisible(hwnd):
        return True
    length = user32.GetClassNameW(hwnd, None, 0)
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetClassNameW(hwnd, buf, length + 1)
    cls = buf.value
    if cls in ("Progman", "WorkerW"):
        return True
    user32.ShowWindow(hwnd, SW_MINIMIZE)
    return True
user32.EnumWindows(enum_proc, 0)
toast(title, text)