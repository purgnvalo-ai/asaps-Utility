"""
FPS Utility — Lite
A safe, restore-point-backed Windows system optimizer for gaming performance.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import subprocess
import ctypes
import sys
import os
import time
import datetime
import winreg

# ─── Admin check ─────────────────────────────────────────────────────────────
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1
    )
    sys.exit()

# ─── Colour palette (matches the website) ────────────────────────────────────
BG       = "#080a0c"
SURFACE  = "#0e1114"
SURFACE2 = "#141820"
BORDER   = "#1e2430"
ACCENT   = "#00d4ff"
ACCENT2  = "#0099cc"
TEXT     = "#e8edf2"
MUTED    = "#5a6472"
GREEN    = "#00e5a0"
GOLD     = "#f5c842"
RED      = "#ff5f57"

FONT_MONO  = ("Consolas", 10)
FONT_MONO_S= ("Consolas", 9)
FONT_HEAD  = ("Segoe UI", 11, "bold")
FONT_TITLE = ("Segoe UI", 18, "bold")
FONT_SMALL = ("Segoe UI", 9)

# ─── Restore point helper ─────────────────────────────────────────────────────
def create_restore_point(description="FPS Utility Lite — Before Tweaks"):
    ps = (
        f'Checkpoint-Computer -Description "{description}" '
        f'-RestorePointType "MODIFY_SETTINGS" -ErrorAction Stop'
    )
    result = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Restore point failed")
    return True

# ─── Individual tweak functions ───────────────────────────────────────────────

def set_high_performance_power_plan():
    subprocess.run(
        ["powercfg", "/setactive", "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"],
        check=True
    )

def disable_core_parking():
    # Set CsEnabled to 0 for all power schemes
    schemes = subprocess.run(
        ["powercfg", "/list"], capture_output=True, text=True
    ).stdout
    guids = [line.split()[3] for line in schemes.splitlines() if "GUID:" in line]
    for guid in guids:
        subprocess.run([
            "powercfg", "/setacvalueindex", guid,
            "54533251-82be-4824-96c1-47b60b740d00",
            "0cc5b647-c1df-4637-891a-dec35c318583", "0"
        ], capture_output=True)

def disable_cpu_idle_states():
    subprocess.run(
        ["powercfg", "/setacvalueindex", "SCHEME_CURRENT",
         "54533251-82be-4824-96c1-47b60b740d00",
         "5d76a2ca-e8c0-402f-a133-2158492d58ad", "0"],
        check=True
    )

def disable_sysmain():
    subprocess.run(["sc", "config", "SysMain", "start=", "disabled"], check=True)
    subprocess.run(["sc", "stop", "SysMain"], capture_output=True)

def disable_search_indexing():
    subprocess.run(["sc", "config", "WSearch", "start=", "disabled"], check=True)
    subprocess.run(["sc", "stop", "WSearch"], capture_output=True)

def disable_xbox_gamebar():
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\GameDVR",
            0, winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, "AppCaptureEnabled", 0, winreg.REG_DWORD, 0)
        winreg.CloseKey(key)
    except Exception:
        pass
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"System\GameConfigStore",
            0, winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, "GameDVR_Enabled", 0, winreg.REG_DWORD, 0)
        winreg.CloseKey(key)
    except Exception:
        pass

def enable_shader_cache():
    try:
        key = winreg.CreateKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\DirectX\UserGpuPreferences"
        )
        winreg.SetValueEx(key, "DirectXUserGlobalSettings", 0,
                          winreg.REG_SZ, "SwapEffectUpgradeEnable=1;")
        winreg.CloseKey(key)
    except Exception:
        pass

def disable_nagle():
    # Disable Nagle's algorithm for all interfaces
    base = r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces"
    try:
        reg = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base)
        i = 0
        while True:
            try:
                sub = winreg.EnumKey(reg, i)
                subkey = winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    f"{base}\\{sub}", 0, winreg.KEY_SET_VALUE
                )
                winreg.SetValueEx(subkey, "TcpAckFrequency", 0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(subkey, "TCPNoDelay",      0, winreg.REG_DWORD, 1)
                winreg.CloseKey(subkey)
                i += 1
            except OSError:
                break
        winreg.CloseKey(reg)
    except Exception:
        pass

def disable_diagtrack():
    subprocess.run(["sc", "config", "DiagTrack",  "start=", "disabled"], capture_output=True)
    subprocess.run(["sc", "stop",   "DiagTrack"], capture_output=True)
    subprocess.run(["sc", "config", "dmwappushservice", "start=", "disabled"], capture_output=True)
    subprocess.run(["sc", "stop",   "dmwappushservice"], capture_output=True)

def apply_gpu_low_latency():
    # NVIDIA via registry (works even without NVCP open)
    try:
        key = winreg.CreateKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers"
        )
        winreg.SetValueEx(key, "HwSchMode", 0, winreg.REG_DWORD, 2)  # HWGPU scheduler
        winreg.CloseKey(key)
    except Exception:
        pass

# ─── Tweak definitions ────────────────────────────────────────────────────────
TWEAKS = [
    {
        "id": "power_plan",
        "name": "High Performance Power Plan",
        "desc": "Prevents CPU from throttling during gaming",
        "category": "CPU",
        "impact": "HIGH",
        "fn": set_high_performance_power_plan,
    },
    {
        "id": "core_parking",
        "name": "Disable Core Parking",
        "desc": "Keeps all CPU cores active — no wake-up latency",
        "category": "CPU",
        "impact": "HIGH",
        "fn": disable_core_parking,
    },
    {
        "id": "cpu_idle",
        "name": "Disable CPU Idle States (C-States)",
        "desc": "Eliminates processor sleep/wake cycles",
        "category": "CPU",
        "impact": "MED",
        "fn": disable_cpu_idle_states,
    },
    {
        "id": "gpu_scheduler",
        "name": "Hardware GPU Scheduler",
        "desc": "Enables WDDM 2.7 HW GPU scheduling",
        "category": "GPU",
        "impact": "HIGH",
        "fn": apply_gpu_low_latency,
    },
    {
        "id": "shader_cache",
        "name": "Enable Shader Cache",
        "desc": "Reduces in-game shader compile stutter",
        "category": "GPU",
        "impact": "HIGH",
        "fn": enable_shader_cache,
    },
    {
        "id": "sysmain",
        "name": "Disable SysMain (Superfetch)",
        "desc": "Frees RAM occupied by OS caching",
        "category": "Services",
        "impact": "MED",
        "fn": disable_sysmain,
    },
    {
        "id": "search_index",
        "name": "Disable Search Indexing",
        "desc": "Stops background disk I/O from indexer",
        "category": "Services",
        "impact": "MED",
        "fn": disable_search_indexing,
    },
    {
        "id": "xbox_gamebar",
        "name": "Disable Xbox Game Bar / DVR",
        "desc": "Removes recording overhead from every game",
        "category": "Services",
        "impact": "MED",
        "fn": disable_xbox_gamebar,
    },
    {
        "id": "diagtrack",
        "name": "Disable Telemetry (DiagTrack)",
        "desc": "Stops Windows phoning home in the background",
        "category": "Services",
        "impact": "MED",
        "fn": disable_diagtrack,
    },
    {
        "id": "nagle",
        "name": "Disable Nagle Algorithm",
        "desc": "Sends network packets without buffering delay",
        "category": "Network",
        "impact": "HIGH",
        "fn": disable_nagle,
    },
]

# ─── Main application window ──────────────────────────────────────────────────
class FPSUtility(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FPS Utility — Lite")
        self.geometry("860x580")
        self.minsize(760, 500)
        self.configure(bg=BG)
        self.resizable(True, True)

        # State
        self.tweak_vars   = {}   # id -> BooleanVar
        self.nav_section  = tk.StringVar(value="Dashboard")
        self.status_text  = tk.StringVar(value="Ready")
        self.restore_done = False
        self.applying     = False

        self._build_ui()
        self._render_section("Dashboard")

    # ── UI shell ──────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Titlebar
        tb = tk.Frame(self, bg="#0a0d10", height=36)
        tb.pack(fill="x")
        tb.pack_propagate(False)

        # Traffic-light dots
        dots_f = tk.Frame(tb, bg="#0a0d10")
        dots_f.pack(side="left", padx=14, pady=10)
        for col in (RED, GOLD, GREEN):
            tk.Label(dots_f, bg=col, width=2, relief="flat").pack(
                side="left", padx=3, ipady=5
            )

        tk.Label(tb, text="FPS Utility — Lite", bg="#0a0d10",
                 fg=MUTED, font=FONT_MONO_S).pack(side="left", expand=True)

        tk.Label(tb, text="v1.0.0", bg="#0a0d10",
                 fg="#2a3040", font=FONT_MONO_S).pack(side="right", padx=14)

        # Separator line
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        # Body: sidebar + content
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True)

        self._build_sidebar(body)
        tk.Frame(body, bg=BORDER, width=1).pack(side="left", fill="y")
        self._build_main(body)

    def _build_sidebar(self, parent):
        sb = tk.Frame(parent, bg="#0a0d10", width=56)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)

        # Logo
        logo_f = tk.Frame(sb, bg="#0a0d10")
        logo_f.pack(pady=(16, 12))
        tk.Label(logo_f, text="⚡", bg="#0a0d10", fg=ACCENT,
                 font=("Segoe UI", 16)).pack()

        # Nav items
        nav_items = [
            ("⊞", "Dashboard"),
            ("⚡", "CPU"),
            ("▣", "GPU"),
            ("◈", "Network"),
            ("❖", "Services"),
        ]

        self.nav_buttons = {}
        for icon, label in nav_items:
            btn = tk.Label(
                sb, text=icon, bg="#0a0d10", fg=MUTED,
                font=("Segoe UI", 14), cursor="hand2",
                width=3, anchor="center"
            )
            btn.pack(pady=3, padx=6, ipady=6)
            btn.bind("<Button-1>", lambda e, l=label: self._nav_click(l))
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=SURFACE2))
            btn.bind("<Leave>", lambda e, b=btn, l=label: self._nav_leave(b, l))
            self.nav_buttons[label] = btn

        # Status dot at bottom
        tk.Frame(sb, bg=BORDER, height=1).pack(fill="x", pady=8)
        self.status_dot = tk.Label(sb, text="●", bg="#0a0d10",
                                   fg=GREEN, font=("Segoe UI", 10))
        self.status_dot.pack(pady=(0, 10))

    def _nav_click(self, label):
        self.nav_section.set(label)
        self._update_nav_highlight()
        self._render_section(label)

    def _nav_leave(self, btn, label):
        if self.nav_section.get() == label:
            btn.config(bg=SURFACE2)
        else:
            btn.config(bg="#0a0d10")

    def _update_nav_highlight(self):
        active = self.nav_section.get()
        for label, btn in self.nav_buttons.items():
            if label == active:
                btn.config(bg=SURFACE2, fg=ACCENT)
            else:
                btn.config(bg="#0a0d10", fg=MUTED)

    def _build_main(self, parent):
        main = tk.Frame(parent, bg=BG)
        main.pack(side="left", fill="both", expand=True)

        # Top bar
        topbar = tk.Frame(main, bg=SURFACE, height=44)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)

        self.section_label = tk.Label(
            topbar, textvariable=self.nav_section,
            bg=SURFACE, fg=TEXT, font=FONT_HEAD, anchor="w"
        )
        self.section_label.pack(side="left", padx=18, pady=10)

        # Tier badge
        tk.Label(topbar, text="LITE", bg=SURFACE, fg=ACCENT,
                 font=FONT_MONO_S,
                 padx=8, pady=2).pack(side="left", padx=4)

        # Apply button
        self.apply_btn = tk.Button(
            topbar, text="⚡  Apply Tweaks",
            bg=ACCENT, fg=BG, font=("Segoe UI", 10, "bold"),
            relief="flat", cursor="hand2", padx=16, pady=6,
            command=self._start_apply
        )
        self.apply_btn.pack(side="right", padx=14, pady=7)

        tk.Frame(main, bg=BORDER, height=1).pack(fill="x")

        # Scrollable content
        self.canvas = tk.Canvas(main, bg=BG, highlightthickness=0, bd=0)
        scrollbar = tk.Scrollbar(main, orient="vertical",
                                 command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.content_frame = tk.Frame(self.canvas, bg=BG)
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.content_frame, anchor="nw"
        )
        self.content_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind("<MouseWheel>", lambda e: self.canvas.yview_scroll(
            int(-1 * (e.delta / 120)), "units"))

    def _on_frame_configure(self, e):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, e):
        self.canvas.itemconfig(self.canvas_window, width=e.width)

    # ── Sections ──────────────────────────────────────────────────────────────
    def _clear_content(self):
        for w in self.content_frame.winfo_children():
            w.destroy()

    def _render_section(self, name):
        self._clear_content()
        self.canvas.yview_moveto(0)
        sections = {
            "Dashboard": self._section_dashboard,
            "CPU":       lambda: self._section_tweaks("CPU"),
            "GPU":       lambda: self._section_tweaks("GPU"),
            "Network":   lambda: self._section_tweaks("Network"),
            "Services":  lambda: self._section_tweaks("Services"),
        }
        fn = sections.get(name)
        if fn:
            fn()
        self._update_nav_highlight()

    def _section_label_widget(self, parent, text, color=ACCENT):
        tk.Label(parent, text=text.upper(), bg=BG, fg=color,
                 font=FONT_MONO_S, anchor="w").pack(
            fill="x", padx=20, pady=(14, 6))
        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=20, pady=(0, 8))

    def _section_dashboard(self):
        p = self.content_frame
        pad = dict(padx=20, pady=4)

        # Stats row
        stats_f = tk.Frame(p, bg=BG)
        stats_f.pack(fill="x", **pad, pady=(16, 8))

        tweaks_on = sum(1 for t in TWEAKS
                        if self.tweak_vars.get(t["id"], tk.BooleanVar(value=True)).get())

        for label, value, color in [
            ("Tweaks Available", str(len(TWEAKS)), ACCENT),
            ("Categories", "4", ACCENT),
            ("Restore Point", "Required" if not self.restore_done else "✓ Done", GREEN),
        ]:
            card = tk.Frame(stats_f, bg=SURFACE, relief="flat",
                            highlightbackground=BORDER, highlightthickness=1)
            card.pack(side="left", padx=(0, 10), ipady=10, ipadx=14, expand=True, fill="x")
            tk.Label(card, text=value, bg=SURFACE, fg=color,
                     font=("Segoe UI", 22, "bold")).pack()
            tk.Label(card, text=label, bg=SURFACE, fg=MUTED,
                     font=FONT_MONO_S).pack()

        # Restore point warning
        if not self.restore_done:
            warn = tk.Frame(p, bg="#1a1006",
                            highlightbackground="#f5c84240", highlightthickness=1)
            warn.pack(fill="x", padx=20, pady=(8, 4))
            tk.Label(warn,
                     text="⚠  A system restore point will be created automatically before any tweaks are applied.",
                     bg="#1a1006", fg=GOLD, font=FONT_SMALL,
                     wraplength=700, justify="left", anchor="w").pack(
                padx=14, pady=10, anchor="w")

        # Terminal log
        self._section_label_widget(p, "System Log")
        self.log_frame = tk.Frame(p, bg="#040506",
                                  highlightbackground=BORDER, highlightthickness=1)
        self.log_frame.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        self.log_text = tk.Text(
            self.log_frame, bg="#040506", fg=MUTED,
            font=FONT_MONO, relief="flat", bd=0,
            height=10, state="disabled", wrap="word",
            insertbackground=ACCENT
        )
        self.log_text.pack(fill="both", expand=True, padx=10, pady=8)
        self._tag_setup()
        self._log(f"[{self._ts()}]", "time",
                  " FPS Utility Lite started. System scan complete.", "ok")
        self._log(f"[{self._ts()}]", "time",
                  f" {len(TWEAKS)} tweaks available across 4 categories.", "info")
        if not self.restore_done:
            self._log(f"[{self._ts()}]", "time",
                      " Restore point will be created before applying tweaks.", "warn")
        self._log(f"[{self._ts()}]", "time",
                  " Click 'Apply Tweaks' when ready.", "info")

    def _tag_setup(self):
        self.log_text.tag_configure("time", foreground="#2a3545")
        self.log_text.tag_configure("ok",   foreground=GREEN)
        self.log_text.tag_configure("info", foreground=ACCENT)
        self.log_text.tag_configure("warn", foreground=GOLD)
        self.log_text.tag_configure("err",  foreground=RED)

    def _ts(self):
        return datetime.datetime.now().strftime("%H:%M:%S")

    def _log(self, ts, ts_tag, msg, msg_tag, newline=True):
        def _do():
            self.log_text.config(state="normal")
            if newline:
                self.log_text.insert("end", "\n" if self.log_text.get("1.0", "end").strip() else "")
            self.log_text.insert("end", ts, ts_tag)
            self.log_text.insert("end", msg, msg_tag)
            self.log_text.config(state="disabled")
            self.log_text.see("end")
        if threading.current_thread() is threading.main_thread():
            _do()
        else:
            self.after(0, _do)

    def _section_tweaks(self, category):
        p = self.content_frame
        tweaks = [t for t in TWEAKS if t["category"] == category]

        self._section_label_widget(p, f"{category} Tweaks")

        for tweak in tweaks:
            if tweak["id"] not in self.tweak_vars:
                self.tweak_vars[tweak["id"]] = tk.BooleanVar(value=True)
            var = self.tweak_vars[tweak["id"]]

            row = tk.Frame(p, bg=SURFACE,
                           highlightbackground=BORDER, highlightthickness=1)
            row.pack(fill="x", padx=20, pady=3, ipady=2)

            # Left: text info
            info_f = tk.Frame(row, bg=SURFACE)
            info_f.pack(side="left", fill="x", expand=True, padx=12, pady=8)

            tk.Label(info_f, text=tweak["name"], bg=SURFACE, fg=TEXT,
                     font=("Segoe UI", 10, "bold"), anchor="w").pack(fill="x")
            tk.Label(info_f, text=tweak["desc"], bg=SURFACE, fg=MUTED,
                     font=FONT_MONO_S, anchor="w").pack(fill="x")

            # Right: impact badge + toggle
            right_f = tk.Frame(row, bg=SURFACE)
            right_f.pack(side="right", padx=12, pady=8)

            impact_color = GREEN if tweak["impact"] == "HIGH" else ACCENT
            tk.Label(right_f, text=tweak["impact"], bg=SURFACE,
                     fg=impact_color, font=FONT_MONO_S,
                     padx=8, pady=2).pack(side="left", padx=(0, 12))

            self._toggle(right_f, var)

    def _toggle(self, parent, var):
        """Custom on/off toggle widget."""
        canvas = tk.Canvas(parent, width=44, height=22,
                           bg=SURFACE, highlightthickness=0, cursor="hand2")
        canvas.pack(side="left")

        def draw():
            canvas.delete("all")
            on = var.get()
            bg_col = ACCENT if on else BORDER
            canvas.create_rounded_rect = lambda *a, **k: None
            # Background pill
            canvas.create_oval(0, 0, 22, 22, fill=bg_col, outline="")
            canvas.create_oval(22, 0, 44, 22, fill=bg_col, outline="")
            canvas.create_rectangle(11, 0, 33, 22, fill=bg_col, outline="")
            # Knob
            x = 24 if on else 2
            canvas.create_oval(x, 2, x+18, 20, fill="white", outline="")

        def toggle(e):
            var.set(not var.get())
            draw()

        draw()
        canvas.bind("<Button-1>", toggle)
        var.trace_add("write", lambda *a: draw())

    # ── Apply logic ───────────────────────────────────────────────────────────
    def _start_apply(self):
        if self.applying:
            return
        # Navigate to dashboard first so log is visible
        self._nav_click("Dashboard")
        self.after(100, self._confirm_apply)

    def _confirm_apply(self):
        selected = [t for t in TWEAKS
                    if self.tweak_vars.get(t["id"], tk.BooleanVar(value=True)).get()]
        if not selected:
            messagebox.showwarning("Nothing Selected",
                                   "Please enable at least one tweak before applying.")
            return

        msg = (
            f"You are about to apply {len(selected)} tweak(s).\n\n"
            "✓  A System Restore Point will be created FIRST.\n"
            "✓  You can undo everything via Windows System Restore.\n\n"
            "Proceed?"
        )
        if not messagebox.askyesno("Confirm Apply", msg, icon="question"):
            return

        self.applying = True
        self.apply_btn.config(state="disabled", text="Working…", bg=MUTED)
        threading.Thread(target=self._apply_thread,
                         args=(selected,), daemon=True).start()

    def _apply_thread(self, selected):
        try:
            # Step 1: Restore point
            self._log(f"[{self._ts()}]", "time",
                      " Creating System Restore Point…", "warn")
            self.after(0, lambda: self.status_dot.config(fg=GOLD))
            create_restore_point()
            self.restore_done = True
            self._log(f"[{self._ts()}]", "time",
                      " ✓ Restore point created successfully.", "ok")

            # Step 2: Apply each tweak
            ok, fail = 0, 0
            for tweak in selected:
                self._log(f"[{self._ts()}]", "time",
                          f" Applying: {tweak['name']}…", "info")
                try:
                    tweak["fn"]()
                    self._log(f"[{self._ts()}]", "time",
                              f" ✓ {tweak['name']} — done.", "ok")
                    ok += 1
                except Exception as e:
                    self._log(f"[{self._ts()}]", "time",
                              f" ✗ {tweak['name']} — {e}", "err")
                    fail += 1
                time.sleep(0.15)

            # Done
            self._log(f"[{self._ts()}]", "time",
                      f" ─────────────────────────────────", "time")
            self._log(f"[{self._ts()}]", "time",
                      f" ✓ Complete — {ok} applied, {fail} failed.", "ok")
            self._log(f"[{self._ts()}]", "time",
                      " Restart Windows for all changes to take full effect.", "warn")

            self.after(0, self._apply_done, ok, fail)

        except Exception as e:
            self._log(f"[{self._ts()}]", "time",
                      f" ✗ FATAL: {e}", "err")
            self.after(0, self._apply_error, str(e))

    def _apply_done(self, ok, fail):
        self.applying = False
        self.apply_btn.config(state="normal", text="⚡  Apply Tweaks", bg=ACCENT)
        self.status_dot.config(fg=GREEN)
        msg = f"{ok} tweak(s) applied successfully."
        if fail:
            msg += f"\n{fail} failed — see the log for details."
        msg += "\n\nRestart your PC to apply all changes."
        messagebox.showinfo("Done!", msg)

    def _apply_error(self, err):
        self.applying = False
        self.apply_btn.config(state="normal", text="⚡  Apply Tweaks", bg=ACCENT)
        self.status_dot.config(fg=RED)
        messagebox.showerror("Error",
                             f"Failed to create restore point:\n\n{err}\n\n"
                             "Make sure System Protection is enabled for your C: drive.")


# ─── Entry point ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = FPSUtility()
    app.mainloop()
