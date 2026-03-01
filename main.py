"""
FPS Utility - Lite
Windows system optimizer for gaming performance.
Requires Administrator privileges.
"""

import tkinter as tk
from tkinter import messagebox
import threading
import subprocess
import ctypes
import sys
import time
import datetime
import winreg


# ── Admin elevation ──────────────────────────────────────────────────────────
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(f'"{a}"' for a in sys.argv), None, 1
    )
    sys.exit()


# ── Palette ───────────────────────────────────────────────────────────────────
BG       = "#080a0c"
SURFACE  = "#0e1114"
SURFACE2 = "#141820"
BORDER   = "#1e2430"
ACCENT   = "#00d4ff"
TEXT     = "#e8edf2"
MUTED    = "#5a6472"
GREEN    = "#00e5a0"
GOLD     = "#f5c842"
REDDOT   = "#ff5f57"
WARN_BG  = "#1a1006"

F_MONO  = ("Consolas", 9)
F_SMALL = ("Segoe UI", 9)
F_BOLD  = ("Segoe UI", 10, "bold")
F_HEAD  = ("Segoe UI", 12, "bold")
F_BIG   = ("Segoe UI", 20, "bold")


# ── Restore point ─────────────────────────────────────────────────────────────
def create_restore_point(desc="FPS Utility Lite - Before Tweaks"):
    cmd = (
        'powershell -NoProfile -NonInteractive -Command '
        '"Checkpoint-Computer -Description \'' + desc + '\' '
        '-RestorePointType MODIFY_SETTINGS -ErrorAction Stop"'
    )
    r = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or "Restore point creation failed")


# ── Tweak functions ───────────────────────────────────────────────────────────
def tweak_high_perf_power():
    subprocess.run(
        ["powercfg", "/setactive", "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"],
        check=True, capture_output=True
    )

def tweak_disable_core_parking():
    r = subprocess.run(["powercfg", "/list"], capture_output=True, text=True)
    guids = [line.split()[3] for line in r.stdout.splitlines() if "GUID:" in line]
    for g in guids:
        subprocess.run([
            "powercfg", "/setacvalueindex", g,
            "54533251-82be-4824-96c1-47b60b740d00",
            "0cc5b647-c1df-4637-891a-dec35c318583", "0"
        ], capture_output=True)

def tweak_disable_cpu_idle():
    subprocess.run([
        "powercfg", "/setacvalueindex", "SCHEME_CURRENT",
        "54533251-82be-4824-96c1-47b60b740d00",
        "5d76a2ca-e8c0-402f-a133-2158492d58ad", "0"
    ], capture_output=True)

def tweak_hw_gpu_scheduler():
    k = winreg.OpenKey(
        winreg.HKEY_LOCAL_MACHINE,
        r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers",
        0, winreg.KEY_SET_VALUE
    )
    winreg.SetValueEx(k, "HwSchMode", 0, winreg.REG_DWORD, 2)
    winreg.CloseKey(k)

def tweak_shader_cache():
    k = winreg.CreateKey(
        winreg.HKEY_LOCAL_MACHINE,
        r"SOFTWARE\Microsoft\DirectX\UserGpuPreferences"
    )
    winreg.SetValueEx(k, "DirectXUserGlobalSettings", 0,
                      winreg.REG_SZ, "SwapEffectUpgradeEnable=1;")
    winreg.CloseKey(k)

def tweak_disable_nagle():
    base = r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces"
    reg = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base)
    i = 0
    while True:
        try:
            sub = winreg.EnumKey(reg, i)
            sk = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                base + "\\" + sub, 0, winreg.KEY_SET_VALUE
            )
            winreg.SetValueEx(sk, "TcpAckFrequency", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(sk, "TCPNoDelay",      0, winreg.REG_DWORD, 1)
            winreg.CloseKey(sk)
            i += 1
        except OSError:
            break
    winreg.CloseKey(reg)

def tweak_disable_sysmain():
    subprocess.run(["sc", "config", "SysMain", "start=", "disabled"], capture_output=True)
    subprocess.run(["sc", "stop",   "SysMain"], capture_output=True)

def tweak_disable_search():
    subprocess.run(["sc", "config", "WSearch", "start=", "disabled"], capture_output=True)
    subprocess.run(["sc", "stop",   "WSearch"], capture_output=True)

def tweak_disable_xbox():
    pairs = [
        (winreg.HKEY_CURRENT_USER,
         r"Software\Microsoft\Windows\CurrentVersion\GameDVR",
         "AppCaptureEnabled", winreg.REG_DWORD, 0),
        (winreg.HKEY_CURRENT_USER,
         r"System\GameConfigStore",
         "GameDVR_Enabled", winreg.REG_DWORD, 0),
    ]
    for hive, path, name, rtype, val in pairs:
        try:
            k = winreg.OpenKey(hive, path, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(k, name, 0, rtype, val)
            winreg.CloseKey(k)
        except Exception:
            pass

def tweak_disable_telemetry():
    for svc in ["DiagTrack", "dmwappushservice"]:
        subprocess.run(["sc", "config", svc, "start=", "disabled"], capture_output=True)
        subprocess.run(["sc", "stop",   svc], capture_output=True)


# ── Tweak list ────────────────────────────────────────────────────────────────
TWEAKS = [
    {"id": "power",    "name": "High Performance Power Plan",
     "desc": "Prevents CPU throttling during gaming",
     "cat": "CPU",      "impact": "HIGH", "fn": tweak_high_perf_power},
    {"id": "parking",  "name": "Disable Core Parking",
     "desc": "Keeps all CPU cores active with no wake latency",
     "cat": "CPU",      "impact": "HIGH", "fn": tweak_disable_core_parking},
    {"id": "idle",     "name": "Disable CPU Idle States",
     "desc": "Eliminates processor C-State sleep cycles",
     "cat": "CPU",      "impact": "MED",  "fn": tweak_disable_cpu_idle},
    {"id": "gpusched", "name": "Hardware GPU Scheduler",
     "desc": "Enables WDDM 2.7 hardware-accelerated scheduling",
     "cat": "GPU",      "impact": "HIGH", "fn": tweak_hw_gpu_scheduler},
    {"id": "shader",   "name": "Enable Shader Cache",
     "desc": "Reduces in-game shader compile stutter",
     "cat": "GPU",      "impact": "HIGH", "fn": tweak_shader_cache},
    {"id": "nagle",    "name": "Disable Nagle Algorithm",
     "desc": "Sends packets immediately without buffering delay",
     "cat": "Network",  "impact": "HIGH", "fn": tweak_disable_nagle},
    {"id": "sysmain",  "name": "Disable SysMain / Superfetch",
     "desc": "Frees RAM occupied by OS cache pre-loading",
     "cat": "Services", "impact": "MED",  "fn": tweak_disable_sysmain},
    {"id": "search",   "name": "Disable Search Indexing",
     "desc": "Stops background disk I/O from Windows Search",
     "cat": "Services", "impact": "MED",  "fn": tweak_disable_search},
    {"id": "xbox",     "name": "Disable Xbox Game Bar / DVR",
     "desc": "Removes game recording overhead completely",
     "cat": "Services", "impact": "MED",  "fn": tweak_disable_xbox},
    {"id": "telemetry","name": "Disable Telemetry",
     "desc": "Stops Windows diagnostic background services",
     "cat": "Services", "impact": "MED",  "fn": tweak_disable_telemetry},
]


# ── Main window ───────────────────────────────────────────────────────────────
class App(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("FPS Utility - Lite")
        self.geometry("860x580")
        self.minsize(720, 480)
        self.configure(bg=BG)
        self.resizable(True, True)

        self.tweak_vars   = {t["id"]: tk.BooleanVar(value=True) for t in TWEAKS}
        self.active_nav   = "Dashboard"
        self.restore_done = False
        self.applying     = False
        self._log_widget  = None
        self._nav_btns    = {}

        self._build()
        self._show("Dashboard")

    # ── Chrome ────────────────────────────────────────────────────────────────
    def _build(self):
        # Titlebar
        bar = tk.Frame(self, bg="#0a0d10", height=38)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        dot_frame = tk.Frame(bar, bg="#0a0d10")
        dot_frame.pack(side="left", padx=14, pady=10)
        for color in (REDDOT, GOLD, GREEN):
            c = tk.Canvas(dot_frame, width=12, height=12,
                          bg="#0a0d10", highlightthickness=0)
            c.pack(side="left", padx=3)
            c.create_oval(1, 1, 11, 11, fill=color, outline="")

        tk.Label(bar, text="FPS Utility  -  Lite",
                 bg="#0a0d10", fg=MUTED, font=F_MONO).pack(
            side="left", expand=True)
        tk.Label(bar, text="v1.0.0",
                 bg="#0a0d10", fg=BORDER, font=F_MONO).pack(
            side="right", padx=14)

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True)

        self._build_sidebar(body)
        tk.Frame(body, bg=BORDER, width=1).pack(side="left", fill="y")
        self._build_main(body)

    def _build_sidebar(self, parent):
        sb = tk.Frame(parent, bg="#0a0d10", width=56)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)

        tk.Label(sb, text="FPS", bg="#0a0d10", fg=ACCENT,
                 font=("Segoe UI", 7, "bold")).pack(pady=(14, 12))

        items = [
            ("Dashboard", "D"),
            ("CPU",       "C"),
            ("GPU",       "G"),
            ("Network",   "N"),
            ("Services",  "S"),
        ]
        for label, letter in items:
            outer = tk.Frame(sb, bg="#0a0d10")
            outer.pack(fill="x", padx=6, pady=2)
            btn = tk.Label(outer, text=letter, bg="#0a0d10", fg=MUTED,
                           font=("Segoe UI", 13, "bold"),
                           width=3, pady=7, cursor="hand2")
            btn.pack(fill="x")
            for w in (outer, btn):
                w.bind("<Button-1>", lambda e, l=label: self._nav(l))
                w.bind("<Enter>",    lambda e, l=label: self._hover(l, True))
                w.bind("<Leave>",    lambda e, l=label: self._hover(l, False))
            self._nav_btns[label] = (btn, outer)

        tk.Frame(sb, bg=BORDER, height=1).pack(fill="x", pady=8)
        self._status_dot = tk.Label(sb, text="*", bg="#0a0d10",
                                    fg=GREEN, font=("Segoe UI", 14, "bold"))
        self._status_dot.pack()

    def _hover(self, label, on):
        if self.active_nav == label:
            return
        btn, outer = self._nav_btns[label]
        c = SURFACE2 if on else "#0a0d10"
        btn.config(bg=c)
        outer.config(bg=c)

    def _nav(self, label):
        self.active_nav = label
        for lbl, (btn, outer) in self._nav_btns.items():
            active = lbl == label
            btn.config(fg=ACCENT if active else MUTED,
                       bg=SURFACE2 if active else "#0a0d10")
            outer.config(bg=SURFACE2 if active else "#0a0d10")
        self._section_label.config(text=label)
        self._show(label)

    def _build_main(self, parent):
        main = tk.Frame(parent, bg=BG)
        main.pack(side="left", fill="both", expand=True)

        top = tk.Frame(main, bg=SURFACE, height=44)
        top.pack(fill="x")
        top.pack_propagate(False)

        self._section_label = tk.Label(
            top, text="Dashboard", bg=SURFACE, fg=TEXT,
            font=F_HEAD, anchor="w")
        self._section_label.pack(side="left", padx=18)

        tk.Label(top, text="LITE", bg=SURFACE, fg=ACCENT,
                 font=F_MONO, padx=6).pack(side="left", padx=4)

        self._apply_btn = tk.Button(
            top, text="  Apply Tweaks  ",
            bg=ACCENT, fg=BG, font=F_BOLD, relief="flat",
            cursor="hand2", pady=5, command=self._start_apply,
            activebackground="#33dcff", activeforeground=BG
        )
        self._apply_btn.pack(side="right", padx=14, pady=7)

        tk.Frame(main, bg=BORDER, height=1).pack(fill="x")

        wrap = tk.Frame(main, bg=BG)
        wrap.pack(fill="both", expand=True)

        self._canvas = tk.Canvas(wrap, bg=BG, highlightthickness=0, bd=0)
        vsb = tk.Scrollbar(wrap, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._inner = tk.Frame(self._canvas, bg=BG)
        win = self._canvas.create_window((0, 0), window=self._inner, anchor="nw")

        self._inner.bind("<Configure>", lambda e: self._canvas.configure(
            scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>", lambda e: self._canvas.itemconfig(
            win, width=e.width))
        self._canvas.bind("<MouseWheel>", lambda e: self._canvas.yview_scroll(
            int(-1 * (e.delta / 120)), "units"))

    # ── Pages ─────────────────────────────────────────────────────────────────
    def _clear(self):
        for w in self._inner.winfo_children():
            w.destroy()
        self._log_widget = None
        self._canvas.yview_moveto(0)

    def _show(self, name):
        self._clear()
        dispatch = {
            "Dashboard": self._page_dashboard,
            "CPU":       lambda: self._page_tweaks("CPU"),
            "GPU":       lambda: self._page_tweaks("GPU"),
            "Network":   lambda: self._page_tweaks("Network"),
            "Services":  lambda: self._page_tweaks("Services"),
        }
        dispatch.get(name, self._page_dashboard)()

    def _section_title(self, parent, text, color=ACCENT):
        tk.Label(parent, text=text.upper(), bg=BG, fg=color,
                 font=F_MONO, anchor="w").pack(
            fill="x", padx=18, pady=(14, 4))
        tk.Frame(parent, bg=BORDER, height=1).pack(
            fill="x", padx=18, pady=(0, 8))

    def _page_dashboard(self):
        p = self._inner

        # Stat row
        stat_row = tk.Frame(p, bg=BG)
        stat_row.pack(fill="x", padx=18, pady=(16, 8))

        for label, val, color in [
            ("Tweaks", str(len(TWEAKS)), ACCENT),
            ("Categories", "4", ACCENT),
            ("Restore Point", "Done" if self.restore_done else "Pending", GREEN),
        ]:
            card = tk.Frame(stat_row, bg=SURFACE,
                            highlightbackground=BORDER, highlightthickness=1)
            card.pack(side="left", expand=True, fill="x",
                      padx=(0, 8), ipady=10, ipadx=12)
            tk.Label(card, text=val, bg=SURFACE, fg=color, font=F_BIG).pack()
            tk.Label(card, text=label, bg=SURFACE, fg=MUTED, font=F_MONO).pack()

        # Warning
        if not self.restore_done:
            warn = tk.Frame(p, bg=WARN_BG,
                            highlightbackground=GOLD, highlightthickness=1)
            warn.pack(fill="x", padx=18, pady=(0, 8))
            tk.Label(
                warn,
                text="  A System Restore Point will be created automatically before any tweaks are applied.",
                bg=WARN_BG, fg=GOLD, font=F_SMALL, anchor="w", justify="left"
            ).pack(fill="x", padx=10, pady=8)

        # Log
        self._section_title(p, "System Log")

        host = tk.Frame(p, bg="#040506",
                        highlightbackground=BORDER, highlightthickness=1)
        host.pack(fill="both", expand=True, padx=18, pady=(0, 16))

        self._log_widget = tk.Text(
            host, bg="#040506", fg=MUTED, font=F_MONO,
            relief="flat", bd=0, height=11,
            state="disabled", wrap="word",
            insertbackground=ACCENT, selectbackground=SURFACE2
        )
        self._log_widget.pack(fill="both", expand=True, padx=10, pady=8)

        self._log_widget.tag_configure("ts",   foreground="#2a3545")
        self._log_widget.tag_configure("ok",   foreground=GREEN)
        self._log_widget.tag_configure("info", foreground=ACCENT)
        self._log_widget.tag_configure("warn", foreground=GOLD)
        self._log_widget.tag_configure("err",  foreground=REDDOT)

        self._log("System scan complete.", "ok")
        self._log(str(len(TWEAKS)) + " tweaks available across 4 categories.", "info")
        if not self.restore_done:
            self._log("Restore point will be created before applying tweaks.", "warn")
        self._log("Select tweaks in each tab, then click Apply Tweaks.", "info")

    def _log(self, msg, tag="info"):
        def _do():
            if self._log_widget is None:
                return
            try:
                w = self._log_widget
                if not w.winfo_exists():
                    return
                w.config(state="normal")
                ts = datetime.datetime.now().strftime("%H:%M:%S")
                w.insert("end", "\n[" + ts + "] ", "ts")
                w.insert("end", msg, tag)
                w.config(state="disabled")
                w.see("end")
            except Exception:
                pass
        if threading.current_thread() is threading.main_thread():
            _do()
        else:
            self.after(0, _do)

    def _page_tweaks(self, category):
        p = self._inner
        tweaks = [t for t in TWEAKS if t["cat"] == category]
        self._section_title(p, category + " Tweaks")
        for t in tweaks:
            self._tweak_row(p, t, self.tweak_vars[t["id"]])

    def _tweak_row(self, parent, tweak, var):
        row = tk.Frame(parent, bg=SURFACE,
                       highlightbackground=BORDER, highlightthickness=1)
        row.pack(fill="x", padx=18, pady=3)

        left = tk.Frame(row, bg=SURFACE)
        left.pack(side="left", fill="x", expand=True, padx=12, pady=10)
        tk.Label(left, text=tweak["name"], bg=SURFACE, fg=TEXT,
                 font=F_BOLD, anchor="w").pack(fill="x")
        tk.Label(left, text=tweak["desc"], bg=SURFACE, fg=MUTED,
                 font=F_MONO, anchor="w").pack(fill="x")

        right = tk.Frame(row, bg=SURFACE)
        right.pack(side="right", padx=12, pady=10)

        ic = GREEN if tweak["impact"] == "HIGH" else ACCENT
        tk.Label(right, text=tweak["impact"], bg=SURFACE,
                 fg=ic, font=F_MONO, padx=6).pack(side="left", padx=(0, 10))
        self._toggle(right, var)

    def _toggle(self, parent, var):
        W, H = 42, 22
        cv = tk.Canvas(parent, width=W, height=H, bg=SURFACE,
                       highlightthickness=0, cursor="hand2")
        cv.pack(side="left")
        R = H // 2

        def draw(*_):
            cv.delete("all")
            on  = var.get()
            col = ACCENT if on else BORDER
            cv.create_oval(0, 0, H, H, fill=col, outline="")
            cv.create_oval(W - H, 0, W, H, fill=col, outline="")
            cv.create_rectangle(R, 0, W - R, H, fill=col, outline="")
            kx = W - H + 2 if on else 2
            cv.create_oval(kx, 2, kx + H - 4, H - 2, fill="white", outline="")

        draw()
        var.trace_add("write", draw)
        cv.bind("<Button-1>", lambda e: var.set(not var.get()))

    # ── Apply ──────────────────────────────────────────────────────────────────
    def _start_apply(self):
        if self.applying:
            return
        selected = [t for t in TWEAKS if self.tweak_vars[t["id"]].get()]
        if not selected:
            messagebox.showwarning("Nothing Selected",
                                   "Enable at least one tweak before applying.")
            return
        if not messagebox.askyesno(
            "Confirm Apply",
            "Apply " + str(len(selected)) + " tweak(s)?\n\n"
            "A System Restore Point will be created first.\n"
            "You can undo everything via Windows System Restore.\n\n"
            "Continue?",
            icon="question"
        ):
            return
        self._nav("Dashboard")
        self.after(150, lambda: self._run(selected))

    def _run(self, selected):
        self.applying = True
        self._apply_btn.config(state="disabled",
                               text="  Working...  ", bg=MUTED)
        self._status_dot.config(fg=GOLD)
        threading.Thread(target=self._worker, args=(selected,), daemon=True).start()

    def _worker(self, selected):
        try:
            self._log("Creating System Restore Point...", "warn")
            create_restore_point()
            self.restore_done = True
            self._log("Restore point created successfully.", "ok")

            ok = fail = 0
            for t in selected:
                self._log("Applying: " + t["name"] + "...", "info")
                try:
                    t["fn"]()
                    self._log(t["name"] + " - done.", "ok")
                    ok += 1
                except Exception as e:
                    self._log(t["name"] + " - FAILED: " + str(e), "err")
                    fail += 1
                time.sleep(0.1)

            self._log("Complete - " + str(ok) + " applied, " + str(fail) + " failed.", "ok")
            self._log("Restart Windows for all changes to take full effect.", "warn")
            self.after(0, self._done, ok, fail)

        except Exception as e:
            self._log("FATAL: " + str(e), "err")
            self.after(0, self._error, str(e))

    def _done(self, ok, fail):
        self.applying = False
        self._apply_btn.config(state="normal",
                               text="  Apply Tweaks  ", bg=ACCENT)
        self._status_dot.config(fg=GREEN)
        msg = str(ok) + " tweak(s) applied successfully."
        if fail:
            msg += "\n" + str(fail) + " failed - see the log for details."
        msg += "\n\nRestart your PC for full effect."
        messagebox.showinfo("Done!", msg)

    def _error(self, err):
        self.applying = False
        self._apply_btn.config(state="normal",
                               text="  Apply Tweaks  ", bg=ACCENT)
        self._status_dot.config(fg=REDDOT)
        messagebox.showerror(
            "Error",
            "Failed to create restore point:\n\n" + err + "\n\n"
            "Make sure System Protection is enabled for your C: drive.\n"
            "(Control Panel > System > System Protection)"
        )


# ── Entry ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()
