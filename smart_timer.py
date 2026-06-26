import time
import os
import ctypes
from ctypes import wintypes
import threading
import tkinter as tk
from PIL import Image
import pystray
from WinToastCreator.creator import toast


class CountdownDialog(tk.Toplevel):
    def __init__(self, master, seconds: int):
        super().__init__(master)
        self.total = max(0, int(seconds))
        self.left = self.total
        self._end_ts = time.time() + self.total
        self._closed = False

        self.title("Таймер уведомления")
        self.resizable(False, False)

        frm = tk.Frame(self, padx=12, pady=12)
        frm.pack(fill="both", expand=True)

        self.lbl = tk.Label(frm, text="", font=("Segoe UI", 16))
        self.lbl.pack(padx=4, pady=(4, 10))

        import tkinter.ttk as ttk
        self.bar = ttk.Progressbar(frm, length=320, mode="determinate", maximum=self.total)
        self.bar.pack(padx=4, pady=(0, 8))

        self.protocol("WM_DELETE_WINDOW", self.close)

        self.transient(master)
        self.grab_set()
        self.focus_force()

        self.update_idletasks()
        if self.master is not None and self.master.winfo_exists():
            x = self.master.winfo_rootx() + (self.master.winfo_width() // 2) - (self.winfo_width() // 2)
            y = self.master.winfo_rooty() + (self.master.winfo_height() // 2) - (self.winfo_height() // 2)
            self.geometry(f"+{x}+{y}")

        self._tick()

    def _format(self, s: int) -> str:
        m, sec = divmod(max(0, s), 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{h:02d}:{m:02d}:{sec:02d}"
        return f"{m:02d}:{sec:02d}"

    def close(self):
        if self._closed:
            return
        self._closed = True
        try:
            self.grab_release()
        except tk.TclError:
            pass
        try:
            self.destroy()
        except tk.TclError:
            pass

    def _tick(self):
        if self._closed:
            return

        now = time.time()
        self.left = max(0, int(round(self._end_ts - now)))

        self.lbl.config(text=f"Осталось: {self._format(self.left)}")
        done = self.total - self.left
        if self.total > 0:
            self.bar["value"] = done

        if self.left <= 0:
            self.lbl.config(text="Время вышло!")
            self.bar["value"] = self.total
            return

        self.after(200, self._tick)


class TimerDialog(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)

        self.title("Таймер уведомления")
        self.resizable(False, False)

        frm = tk.Frame(self, padx=12, pady=12)
        frm.pack(fill="both", expand=True)

        tk.Label(frm, text="Часы:").grid(row=0, column=0, sticky="e")
        self.eh = tk.Entry(frm, width=8)
        self.eh.grid(row=0, column=1, sticky="w")
        self.eh.insert(0, "0")

        tk.Label(frm, text="Минуты:").grid(row=1, column=0, sticky="e")
        self.em = tk.Entry(frm, width=8)
        self.em.grid(row=1, column=1, sticky="w")
        self.em.insert(0, "0")

        tk.Label(frm, text="Секунды:").grid(row=2, column=0, sticky="e")
        self.es = tk.Entry(frm, width=8)
        self.es.grid(row=2, column=1, sticky="w")
        self.es.insert(0, "10")

        tk.Label(frm, text="Заголовок:").grid(row=3, column=0, sticky="ne", pady=(10, 0))
        self.title_e = tk.Entry(frm, width=35)
        self.title_e.grid(row=3, column=1, sticky="w", pady=(10, 0))
        self.title_e.insert(0, "Уведомление")

        tk.Label(frm, text="Текст:").grid(row=4, column=0, sticky="ne", pady=(8, 0))
        self.text_e = tk.Text(frm, width=35, height=5)
        self.text_e.grid(row=4, column=1, sticky="w", pady=(8, 0))

        btns = tk.Frame(frm)
        btns.grid(row=5, column=0, columnspan=2, pady=(12, 0), sticky="ew")

        tk.Button(btns, text="Запустить", command=self.start).pack(side="left")
        tk.Button(btns, text="Отмена", command=self.destroy).pack(side="right")

        self.update_idletasks()
        if master is not None and master.winfo_exists():
            x = master.winfo_rootx() + (master.winfo_width() // 2) - (self.winfo_width() // 2)
            y = master.winfo_rooty() + (master.winfo_height() // 2) - (self.winfo_height() // 2)
            self.geometry(f"+{x}+{y}")

        self.grab_set()
        self.eh.focus_set()

    def _read_delay(self) -> int:
        h = int(self.eh.get().strip() or "0")
        m = int(self.em.get().strip() or "0")
        s = int(self.es.get().strip() or "0")
        if h < 0 or m < 0 or s < 0:
            raise ValueError
        d = h * 3600 + m * 60 + s
        if d <= 0:
            raise ValueError
        return d


    def start(self):
        try:
            d = self._read_delay()
            title = self.title_e.get().strip()
            text = self.text_e.get("1.0", "end").strip()

            if not title:
                tk.messagebox.showerror("Ошибка", "Укажите заголовок.")
                return
            if not text:
                tk.messagebox.showerror("Ошибка", "Укажите текст уведомления.")
                return
        except Exception:
            tk.messagebox.showerror("Ошибка", "Проверьте введённые значения времени.")
            return

        self.withdraw()

        def open_dialog():
            CountdownDialog(self.master, d)

        self.after(0, open_dialog)

        def worker():
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

            try:
                self.after(0, self.destroy)
            except tk.TclError:
                pass

        threading.Thread(target=worker, daemon=True).start()


def main():
    root = tk.Tk()
    root.withdraw()

    import tkinter.messagebox as messagebox
    import tkinter.ttk as ttk  
    tk.messagebox = messagebox

    image = Image.open("icon.png")

    def action1(icon, item):
        TimerDialog(root)

    def on_quit(icon, item):
        icon.stop()
        os._exit(0)

    menu = pystray.Menu(
        pystray.MenuItem("Изменение таймера", action1),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Выход", on_quit),
    )

    icon = pystray.Icon("my_app", image, "Моё приложение", menu=menu)
    threading.Thread(target=icon.run, daemon=True).start()

    root.mainloop()


if __name__ == "__main__":
    main()
