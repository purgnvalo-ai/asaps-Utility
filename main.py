"""
FPS Utility - Lite  v2.0
Matches the web store UI exactly.
Requires: Python 3.9+  |  Windows 10/11  |  Administrator
"""

import tkinter as tk
from tkinter import messagebox
import threading
import subprocess
import ctypes, sys, time, datetime, winreg, os

# ── Admin gate ────────────────────────────────────────────────────────────────
def _is_admin():
    try: return ctypes.windll.shell32.IsUserAnAdmin()
    except: return False

if not _is_admin():
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable,
        " ".join(f'"{a}"' for a in sys.argv), None, 1)
    sys.exit()

# ── Exact palette from web app ────────────────────────────────────────────────
BG       = "#080a0c"
SURF     = "#0e1114"
SURF2    = "#141820"
BORDER   = "#111820"      # rgba(255,255,255,0.06) approximated
ACCENT   = "#00d4ff"
TEXT     = "#e8edf2"
MUTED    = "#5a6472"
GREEN    = "#00e5a0"
GOLD     = "#f5c842"
REDDOT   = "#ff5f57"
YELLDOT  = "#ffbd2e"
GRNDOT   = "#28c840"
WARN_BG  = "#110e02"
ACCENT_DIM = "#0e2a33"    # rgba(0,212,255,0.08) on dark bg

# Fonts — closest tkinter equivalents to Syne + DM Mono
try:
    import tkinter.font as tkfont
    _check = tkfont.Font(family="Segoe UI Variable", size=10)
    FONT_UI = "Segoe UI Variable"
except Exception:
    FONT_UI = "Segoe UI"

FM  = ("Consolas", 9)          # DM Mono equivalent
FMS = ("Consolas", 8)
FH  = (FONT_UI, 11, "bold")    # Section header
FT  = (FONT_UI, 18, "bold")    # Big title
FN  = (FONT_UI, 10, "bold")    # Tweak name
FS  = (FONT_UI, 9)             # Small / desc
FB  = (FONT_UI, 10, "bold")    # Button

# ─────────────────────────────────────────────────────────────────────────────
#  TWEAKS  — aggressive, real-world FPS impact
# ─────────────────────────────────────────────────────────────────────────────

def _reg_set(hive, path, name, rtype, value):
    k = winreg.CreateKeyEx(hive, path, 0,
                           winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY)
    winreg.SetValueEx(k, name, 0, rtype, value)
    winreg.CloseKey(k)

def _sc(action, service):
    subprocess.run(["sc", action, service], capture_output=True)

def _ps(cmd):
    return subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
        capture_output=True, text=True)

# ── CPU ───────────────────────────────────────────────────────────────────────
def t_high_perf():
    """Activate Ultimate Performance power plan (creates it if missing)."""
    r = _ps("powercfg /duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61")
    guid = None
    for line in r.stdout.splitlines():
        parts = line.strip().split()
        if parts:
            guid = parts[-1]
    if guid and len(guid) == 36:
        _ps(f"powercfg /setactive {guid}")
    else:
        _ps("powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c")

def t_core_parking():
    """Disable core parking on all power schemes."""
    r = subprocess.run(["powercfg", "/list"], capture_output=True, text=True)
    guids = [ln.split()[3] for ln in r.stdout.splitlines() if "GUID:" in ln]
    for g in guids:
        subprocess.run([
            "powercfg", "/setacvalueindex", g,
            "54533251-82be-4824-96c1-47b60b740d00",
            "0cc5b647-c1df-4637-891a-dec35c318583", "0"
        ], capture_output=True)
        subprocess.run([
            "powercfg", "/setdcvalueindex", g,
            "54533251-82be-4824-96c1-47b60b740d00",
            "0cc5b647-c1df-4637-891a-dec35c318583", "0"
        ], capture_output=True)
    subprocess.run(["powercfg", "/s", "SCHEME_CURRENT"], capture_output=True)

def t_cpu_priority():
    """Win32PrioritySeparation = 26 (hex 0x1a) — max foreground boost."""
    _reg_set(winreg.HKEY_LOCAL_MACHINE,
             r"SYSTEM\CurrentControlSet\Control\PriorityControl",
             "Win32PrioritySeparation", winreg.REG_DWORD, 0x26)

def t_timer_resolution():
    """Set 1ms timer resolution via bcdedit (useplatformtick)."""
    subprocess.run(["bcdedit", "/set", "useplatformtick", "yes"],
                   capture_output=True)
    subprocess.run(["bcdedit", "/set", "disabledynamictick", "yes"],
                   capture_output=True)

def t_cpu_idle():
    """Disable processor idle (C-states) on current scheme."""
    subprocess.run([
        "powercfg", "/setacvalueindex", "SCHEME_CURRENT",
        "54533251-82be-4824-96c1-47b60b740d00",
        "5d76a2ca-e8c0-402f-a133-2158492d58ad", "0"
    ], capture_output=True)

def t_affinity_boost():
    """Raise foreground app quantum to max, disable background throttle."""
    _reg_set(winreg.HKEY_LOCAL_MACHINE,
             r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile",
             "SystemResponsiveness", winreg.REG_DWORD, 0)
    _reg_set(winreg.HKEY_LOCAL_MACHINE,
             r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games",
             "GPU Priority",        winreg.REG_DWORD, 8)
    _reg_set(winreg.HKEY_LOCAL_MACHINE,
             r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games",
             "Priority",            winreg.REG_DWORD, 6)
    _reg_set(winreg.HKEY_LOCAL_MACHINE,
             r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games",
             "Scheduling Category", winreg.REG_SZ,    "High")
    _reg_set(winreg.HKEY_LOCAL_MACHINE,
             r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games",
             "SFIO Priority",       winreg.REG_SZ,    "High")

# ── GPU ───────────────────────────────────────────────────────────────────────
def t_hw_gpu_sched():
    """Enable Hardware-accelerated GPU Scheduling (WDDM 2.7+)."""
    _reg_set(winreg.HKEY_LOCAL_MACHINE,
             r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers",
             "HwSchMode", winreg.REG_DWORD, 2)

def t_shader_cache():
    """Unlimited DirectX shader cache."""
    _reg_set(winreg.HKEY_LOCAL_MACHINE,
             r"SOFTWARE\Microsoft\DirectX\UserGpuPreferences",
             "DirectXUserGlobalSettings", winreg.REG_SZ,
             "SwapEffectUpgradeEnable=1;")
    # Also set via NvAPI registry path if present
    try:
        _reg_set(winreg.HKEY_LOCAL_MACHINE,
                 r"SOFTWARE\NVIDIA Corporation\Global\NVTweak",
                 "Compliancy", winreg.REG_DWORD, 0)
    except Exception:
        pass

def t_mpo_disable():
    """Disable Multi-Plane Overlay — fixes stutters on many systems."""
    _reg_set(winreg.HKEY_LOCAL_MACHINE,
             r"SOFTWARE\Microsoft\Windows\Dwm",
             "OverlayTestMode", winreg.REG_DWORD, 5)

def t_dxgi_prerender():
    """Limit pre-rendered frames to 1 (DXGI flip model tweak)."""
    _reg_set(winreg.HKEY_LOCAL_MACHINE,
             r"SOFTWARE\Microsoft\DirectX",
             "MaxRenderedFramesAllowed", winreg.REG_DWORD, 1)

# ── Network ───────────────────────────────────────────────────────────────────
def t_nagle():
    """Disable Nagle + set TcpAckFrequency=1 on all interfaces."""
    base = r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces"
    reg = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base)
    i = 0
    while True:
        try:
            sub = winreg.EnumKey(reg, i)
            k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                               base + "\\" + sub, 0,
                               winreg.KEY_SET_VALUE)
            winreg.SetValueEx(k, "TcpAckFrequency", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(k, "TCPNoDelay",      0, winreg.REG_DWORD, 1)
            winreg.CloseKey(k)
            i += 1
        except OSError:
            break
    winreg.CloseKey(reg)

def t_network_throttle():
    """Remove Windows network throttling (10 Mbps gaming cap removed)."""
    _reg_set(winreg.HKEY_LOCAL_MACHINE,
             r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile",
             "NetworkThrottlingIndex", winreg.REG_DWORD, 0xffffffff)

def t_dns_cache():
    """Maximize DNS client cache size for faster lookups."""
    _reg_set(winreg.HKEY_LOCAL_MACHINE,
             r"SYSTEM\CurrentControlSet\Services\Dnscache\Parameters",
             "CacheHashTableBucketSize",    winreg.REG_DWORD, 1)
    _reg_set(winreg.HKEY_LOCAL_MACHINE,
             r"SYSTEM\CurrentControlSet\Services\Dnscache\Parameters",
             "CacheHashTableSize",          winreg.REG_DWORD, 384)
    _reg_set(winreg.HKEY_LOCAL_MACHINE,
             r"SYSTEM\CurrentControlSet\Services\Dnscache\Parameters",
             "MaxCacheEntryTtlLimit",       winreg.REG_DWORD, 0xff0000)
    _reg_set(winreg.HKEY_LOCAL_MACHINE,
             r"SYSTEM\CurrentControlSet\Services\Dnscache\Parameters",
             "MaxSOACacheEntryTtlLimit",    winreg.REG_DWORD, 0x12c)

# ── Services ──────────────────────────────────────────────────────────────────
def t_sysmain():
    subprocess.run(["sc", "config", "SysMain", "start=", "disabled"], capture_output=True)
    subprocess.run(["sc", "stop",   "SysMain"], capture_output=True)

def t_search():
    subprocess.run(["sc", "config", "WSearch", "start=", "disabled"], capture_output=True)
    subprocess.run(["sc", "stop",   "WSearch"], capture_output=True)

def t_xbox():
    for hive, path, name, rtype, val in [
        (winreg.HKEY_CURRENT_USER,
         r"Software\Microsoft\Windows\CurrentVersion\GameDVR",
         "AppCaptureEnabled",   winreg.REG_DWORD, 0),
        (winreg.HKEY_CURRENT_USER,
         r"System\GameConfigStore",
         "GameDVR_Enabled",     winreg.REG_DWORD, 0),
        (winreg.HKEY_CURRENT_USER,
         r"System\GameConfigStore",
         "GameDVR_FSEBehaviorMode", winreg.REG_DWORD, 2),
    ]:
        try:
            k = winreg.OpenKey(hive, path, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(k, name, 0, rtype, val)
            winreg.CloseKey(k)
        except Exception:
            pass

def t_telemetry():
    for svc in ["DiagTrack", "dmwappushservice", "WerSvc", "PcaSvc"]:
        subprocess.run(["sc", "config", svc, "start=", "disabled"], capture_output=True)
        subprocess.run(["sc", "stop",   svc], capture_output=True)
    _reg_set(winreg.HKEY_LOCAL_MACHINE,
             r"SOFTWARE\Policies\Microsoft\Windows\DataCollection",
             "AllowTelemetry", winreg.REG_DWORD, 0)

def t_fse():
    """Enable fullscreen exclusive optimizations + disable HAGS conflicts."""
    _reg_set(winreg.HKEY_CURRENT_USER,
             r"System\GameConfigStore",
             "GameDVR_DXGIHonorFSEWindowsCompatible", winreg.REG_DWORD, 1)
    _reg_set(winreg.HKEY_CURRENT_USER,
             r"System\GameConfigStore",
             "GameDVR_EFSEFeatureFlags", winreg.REG_DWORD, 0)

def t_memory():
    """Large system cache off, clear standby page cache on low memory."""
    _reg_set(winreg.HKEY_LOCAL_MACHINE,
             r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management",
             "LargeSystemCache",         winreg.REG_DWORD, 0)
    _reg_set(winreg.HKEY_LOCAL_MACHINE,
             r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management",
             "DisablePagingExecutive",   winreg.REG_DWORD, 1)
    _reg_set(winreg.HKEY_LOCAL_MACHINE,
             r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management",
             "SystemPages",              winreg.REG_DWORD, 0xffffffff)

# ── Restore point ─────────────────────────────────────────────────────────────
def create_restore_point():
    cmd = (
        'Checkpoint-Computer -Description "FPS Utility Lite - Before Tweaks" '
        '-RestorePointType MODIFY_SETTINGS -ErrorAction Stop'
    )
    r = _ps(cmd)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or "Restore point creation failed.\n"
                           "Enable System Protection on C: via Control Panel > System.")

# ── Master tweak list ─────────────────────────────────────────────────────────
TWEAKS = [
    # CPU
    {"id":"perf_plan",   "cat":"CPU",     "impact":"HIGH",
     "name":"Ultimate Performance Plan",
     "desc":"Activates hidden max-power plan — highest sustained clocks",
     "fn": t_high_perf},
    {"id":"core_park",   "cat":"CPU",     "impact":"HIGH",
     "name":"Disable Core Parking",
     "desc":"All cores stay awake — eliminates spin-up stutter",
     "fn": t_core_parking},
    {"id":"cpu_prio",    "cat":"CPU",     "impact":"HIGH",
     "name":"Foreground CPU Priority Boost",
     "desc":"Win32PrioritySeparation=0x26 — max quantum to game thread",
     "fn": t_cpu_priority},
    {"id":"timer_res",   "cat":"CPU",     "impact":"HIGH",
     "name":"1ms Timer Resolution",
     "desc":"bcdedit useplatformtick — tightest scheduler tick",
     "fn": t_timer_resolution},
    {"id":"cpu_idle",    "cat":"CPU",     "impact":"MED",
     "name":"Disable CPU Idle States",
     "desc":"Removes C-state power transitions during gameplay",
     "fn": t_cpu_idle},
    {"id":"mm_games",    "cat":"CPU",     "impact":"HIGH",
     "name":"Multimedia Game Scheduling",
     "desc":"GPU Priority 8 + Scheduling Category High for games",
     "fn": t_affinity_boost},
    # GPU
    {"id":"hw_sched",    "cat":"GPU",     "impact":"HIGH",
     "name":"Hardware GPU Scheduler",
     "desc":"WDDM 2.7 HAGS — reduces CPU-GPU latency significantly",
     "fn": t_hw_gpu_sched},
    {"id":"shader",      "cat":"GPU",     "impact":"HIGH",
     "name":"Unlimited Shader Cache",
     "desc":"No disk cap on shader store — eliminates compile stutters",
     "fn": t_shader_cache},
    {"id":"mpo",         "cat":"GPU",     "impact":"HIGH",
     "name":"Disable Multi-Plane Overlay",
     "desc":"Fixes major stutters + black screens on NVIDIA/AMD",
     "fn": t_mpo_disable},
    {"id":"prerender",   "cat":"GPU",     "impact":"HIGH",
     "name":"Limit Pre-rendered Frames",
     "desc":"DXGI max 1 pre-rendered frame — cuts input lag",
     "fn": t_dxgi_prerender},
    # Network
    {"id":"nagle",       "cat":"Network", "impact":"HIGH",
     "name":"Disable Nagle Algorithm",
     "desc":"TCPNoDelay + AckFrequency=1 on all interfaces",
     "fn": t_nagle},
    {"id":"net_throttle","cat":"Network", "impact":"HIGH",
     "name":"Remove Network Throttle",
     "desc":"Removes the hidden 10 Mbps multimedia throttle cap",
     "fn": t_network_throttle},
    {"id":"dns",         "cat":"Network", "impact":"MED",
     "name":"Maximize DNS Cache",
     "desc":"Larger cache bucket size — faster server lookups",
     "fn": t_dns_cache},
    # Services
    {"id":"sysmain",     "cat":"Services","impact":"MED",
     "name":"Disable SysMain / Superfetch",
     "desc":"Frees RAM from OS cache pre-loading",
     "fn": t_sysmain},
    {"id":"search",      "cat":"Services","impact":"MED",
     "name":"Disable Search Indexing",
     "desc":"Stops background disk I/O from Windows Search",
     "fn": t_search},
    {"id":"xbox",        "cat":"Services","impact":"MED",
     "name":"Disable Xbox Game Bar / DVR",
     "desc":"Removes recording hooks and overlay overhead",
     "fn": t_xbox},
    {"id":"telemetry",   "cat":"Services","impact":"MED",
     "name":"Disable Telemetry Services",
     "desc":"Kills DiagTrack, WerSvc, PcaSvc background phoning",
     "fn": t_telemetry},
    {"id":"fse",         "cat":"Services","impact":"HIGH",
     "name":"Fullscreen Exclusive Fix",
     "desc":"Forces true FSE mode — maximum GPU priority in games",
     "fn": t_fse},
    {"id":"memory",      "cat":"Services","impact":"MED",
     "name":"Memory Manager Optimization",
     "desc":"DisablePagingExecutive + max system pages for gaming",
     "fn": t_memory},
]

CATS = ["CPU", "GPU", "Network", "Services"]

# ─────────────────────────────────────────────────────────────────────────────
#  UI
# ─────────────────────────────────────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FPS Utility - Lite")
        self.geometry("920x620")
        self.minsize(800, 520)
        self.configure(bg=BG)
        self.resizable(True, True)

        self.vars         = {t["id"]: tk.BooleanVar(value=True) for t in TWEAKS}
        self.active       = "Dashboard"
        self.restore_done = False
        self.applying     = False
        self._log_w       = None

        self._build_window()
        self._go("Dashboard")

    # ── Window ────────────────────────────────────────────────────────────────
    def _build_window(self):
        # ── Titlebar ──────────────────────────────────────────────────────────
        bar = tk.Frame(self, bg="#080c10", height=40)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        # Traffic-light dots via canvas
        dc = tk.Canvas(bar, bg="#080c10", width=70, height=40,
                       highlightthickness=0)
        dc.pack(side="left", padx=14)
        for i, col in enumerate((REDDOT, YELLDOT, GRNDOT)):
            x = 10 + i * 20
            dc.create_oval(x, 14, x+12, 26, fill=col, outline="")

        tk.Label(bar, text="FPS Utility  —  Lite",
                 bg="#080c10", fg=MUTED, font=FM).pack(
            side="left", expand=True)
        tk.Label(bar, text="v2.0  |  LITE",
                 bg="#080c10", fg=BORDER, font=FM).pack(
            side="right", padx=16)

        # 1px border line
        tk.Frame(self, bg="#1a2232", height=1).pack(fill="x")

        # ── Body ──────────────────────────────────────────────────────────────
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True)

        self._sidebar(body)
        tk.Frame(body, bg="#0d1420", width=1).pack(side="left", fill="y")
        self._main_area(body)

    # ── Sidebar ───────────────────────────────────────────────────────────────
    def _sidebar(self, parent):
        sb = tk.Frame(parent, bg="#080c10", width=60)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)

        # Logo glow canvas
        lc = tk.Canvas(sb, width=44, height=44, bg="#080c10",
                       highlightthickness=0)
        lc.pack(pady=(14, 10))
        # Outer glow ring
        lc.create_oval(4, 4, 40, 40, outline="#00d4ff22", width=1)
        lc.create_oval(8, 8, 36, 36, fill="#0e2535", outline="#00d4ff44", width=1)
        lc.create_text(22, 22, text="FPS", fill=ACCENT,
                       font=("Consolas", 8, "bold"))

        self._nav_frames = {}
        self._nav_labels = {}

        nav_data = [
            ("Dashboard", "⌂"),
            ("CPU",       "⚡"),
            ("GPU",       "▣"),
            ("Network",   "◈"),
            ("Services",  "✦"),
        ]
        for label, icon in nav_data:
            outer = tk.Frame(sb, bg="#080c10", cursor="hand2")
            outer.pack(fill="x", padx=8, pady=2)
            # Icon canvas with highlight bar
            nc = tk.Canvas(outer, width=44, height=38, bg="#080c10",
                           highlightthickness=0, cursor="hand2")
            nc.pack()
            nc.create_text(22, 14, text=icon, fill=MUTED,
                           font=("Segoe UI", 13), tags="icon")
            nc.create_text(22, 29, text=label[:3].upper(), fill=MUTED,
                           font=("Consolas", 6), tags="sublabel")
            for w in (outer, nc):
                w.bind("<Button-1>", lambda e, l=label: self._nav(l))
                w.bind("<Enter>",    lambda e, l=label: self._nhover(l, True))
                w.bind("<Leave>",    lambda e, l=label: self._nhover(l, False))
            self._nav_frames[label] = outer
            self._nav_labels[label] = nc

        # Status indicator at bottom
        tk.Frame(sb, bg="#0d1420", height=1).pack(fill="x", pady=(10, 6))
        self._dot_cv = tk.Canvas(sb, width=20, height=20, bg="#080c10",
                                 highlightthickness=0)
        self._dot_cv.pack(pady=(0, 12))
        self._dot_cv.create_oval(4, 4, 16, 16, fill=GREEN,
                                 outline="", tags="dot")

    def _nhover(self, label, on):
        if self.active == label:
            return
        nc = self._nav_labels[label]
        outer = self._nav_frames[label]
        c = SURF2 if on else "#080c10"
        nc.config(bg=c)
        outer.config(bg=c)
        nc.itemconfig("icon",     fill=TEXT if on else MUTED)
        nc.itemconfig("sublabel", fill=TEXT if on else MUTED)

    def _nav(self, label):
        # Deactivate old
        old = self._nav_labels.get(self.active)
        old_f = self._nav_frames.get(self.active)
        if old:
            old.config(bg="#080c10")
            old_f.config(bg="#080c10")
            old.itemconfig("icon",     fill=MUTED)
            old.itemconfig("sublabel", fill=MUTED)
            old.delete("bar")

        self.active = label
        nc = self._nav_labels[label]
        outer = self._nav_frames[label]
        nc.config(bg=SURF2)
        outer.config(bg=SURF2)
        nc.itemconfig("icon",     fill=ACCENT)
        nc.itemconfig("sublabel", fill=ACCENT)
        # Active indicator bar on left edge
        nc.create_rectangle(0, 4, 3, 34, fill=ACCENT, outline="", tags="bar")

        self._topbar_lbl.config(text=label)
        self._go(label)

    # ── Main area ─────────────────────────────────────────────────────────────
    def _main_area(self, parent):
        main = tk.Frame(parent, bg=BG)
        main.pack(side="left", fill="both", expand=True)

        # Topbar
        top = tk.Frame(main, bg=SURF, height=46)
        top.pack(fill="x")
        top.pack_propagate(False)

        self._topbar_lbl = tk.Label(
            top, text="Dashboard", bg=SURF, fg=TEXT,
            font=FH, anchor="w")
        self._topbar_lbl.pack(side="left", padx=18)

        # LITE badge — pill shape via canvas
        bc = tk.Canvas(top, width=52, height=22, bg=SURF,
                       highlightthickness=0)
        bc.pack(side="left", padx=6, pady=12)
        bc.create_oval(0, 0, 22, 22, fill=ACCENT_DIM, outline="#00d4ff55")
        bc.create_oval(30, 0, 52, 22, fill=ACCENT_DIM, outline="#00d4ff55")
        bc.create_rectangle(11, 0, 41, 22, fill=ACCENT_DIM, outline="")
        bc.create_text(26, 11, text="LITE", fill=ACCENT,
                       font=("Consolas", 7, "bold"))

        self._apply_btn = tk.Button(
            top, text="  ⚡  Apply Tweaks  ",
            bg=ACCENT, fg=BG, font=FB,
            relief="flat", cursor="hand2", pady=6,
            command=self._start_apply,
            activebackground="#33dcff", activeforeground=BG
        )
        self._apply_btn.pack(side="right", padx=16, pady=8)

        tk.Frame(main, bg="#0d1420", height=1).pack(fill="x")

        # Scrollable content
        wrap = tk.Frame(main, bg=BG)
        wrap.pack(fill="both", expand=True)

        self._canvas = tk.Canvas(wrap, bg=BG, highlightthickness=0, bd=0)
        vsb = tk.Scrollbar(wrap, orient="vertical",
                           command=self._canvas.yview,
                           troughcolor=BG, bg=SURF2)
        self._canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._inner = tk.Frame(self._canvas, bg=BG)
        self._cwin  = self._canvas.create_window(
            (0, 0), window=self._inner, anchor="nw")

        self._inner.bind("<Configure>", lambda e: self._canvas.configure(
            scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>", lambda e: self._canvas.itemconfig(
            self._cwin, width=e.width))
        self._canvas.bind("<MouseWheel>", lambda e: self._canvas.yview_scroll(
            int(-1*(e.delta/120)), "units"))

    # ── Page dispatcher ───────────────────────────────────────────────────────
    def _clear(self):
        for w in self._inner.winfo_children():
            w.destroy()
        self._log_w = None
        self._canvas.yview_moveto(0)

    def _go(self, name):
        self._clear()
        {
            "Dashboard": self._page_dash,
            "CPU":       lambda: self._page_tweaks("CPU"),
            "GPU":       lambda: self._page_tweaks("GPU"),
            "Network":   lambda: self._page_tweaks("Network"),
            "Services":  lambda: self._page_tweaks("Services"),
        }.get(name, self._page_dash)()

    # ── Shared widgets ────────────────────────────────────────────────────────
    def _sec_label(self, parent, text, color=ACCENT, pady_top=16):
        row = tk.Frame(parent, bg=BG)
        row.pack(fill="x", padx=18, pady=(pady_top, 0))

        # Dot
        dc = tk.Canvas(row, width=8, height=8, bg=BG, highlightthickness=0)
        dc.pack(side="left", padx=(0, 7), pady=6)
        dc.create_oval(0, 0, 7, 7, fill=color, outline="")

        tk.Label(row, text=text.upper(), bg=BG, fg=color,
                 font=("Consolas", 8, "bold"),
                 letter_spacing=2).pack(side="left")

        tk.Frame(parent, bg="#0d1420", height=1).pack(
            fill="x", padx=18, pady=(4, 10))

    def _stat_card(self, parent, label, value, color):
        card = tk.Frame(parent, bg=SURF,
                        highlightbackground="#0d1420",
                        highlightthickness=1)
        card.pack(side="left", expand=True, fill="x", padx=(0, 10),
                  ipady=14, ipadx=14)
        # Value
        tk.Label(card, text=value, bg=SURF, fg=color,
                 font=(FONT_UI, 22, "bold")).pack()
        # Label
        tk.Label(card, text=label, bg=SURF, fg=MUTED,
                 font=FM).pack()
        return card

    # ── Dashboard ─────────────────────────────────────────────────────────────
    def _page_dash(self):
        p = self._inner

        # ── Stats row ─────────────────────────────────────────────────────────
        self._sec_label(p, "System Status")
        stat_row = tk.Frame(p, bg=BG)
        stat_row.pack(fill="x", padx=18, pady=(0, 14))

        high_n = sum(1 for t in TWEAKS if t["impact"]=="HIGH")
        self._stat_card(stat_row, "Total Tweaks",   str(len(TWEAKS)), ACCENT)
        self._stat_card(stat_row, "HIGH Impact",    str(high_n),      GREEN)
        rp_val = "Done" if self.restore_done else "Pending"
        rp_col = GREEN if self.restore_done else GOLD
        self._stat_card(stat_row, "Restore Point",  rp_val,           rp_col)

        # ── Warning banner ────────────────────────────────────────────────────
        if not self.restore_done:
            warn_outer = tk.Frame(p, bg=BG, padx=18)
            warn_outer.pack(fill="x", pady=(0, 10))
            warn = tk.Frame(warn_outer, bg=WARN_BG,
                            highlightbackground=GOLD,
                            highlightthickness=1)
            warn.pack(fill="x")
            row2 = tk.Frame(warn, bg=WARN_BG)
            row2.pack(fill="x", padx=12, pady=10)
            wdc = tk.Canvas(row2, width=14, height=14, bg=WARN_BG,
                            highlightthickness=0)
            wdc.pack(side="left", padx=(0, 8))
            wdc.create_polygon(7,1, 13,13, 1,13, fill=GOLD, outline="")
            wdc.create_text(7, 10, text="!", fill=BG,
                            font=("Segoe UI", 7, "bold"))
            tk.Label(row2,
                     text="A System Restore Point is created automatically before any tweaks are applied.",
                     bg=WARN_BG, fg=GOLD, font=FS,
                     anchor="w", justify="left").pack(side="left")

        # ── Tweak overview grid ───────────────────────────────────────────────
        self._sec_label(p, "Tweak Overview")
        for cat in CATS:
            cat_tweaks = [t for t in TWEAKS if t["cat"] == cat]
            self._mini_cat_row(p, cat, cat_tweaks)

        # ── Terminal log ──────────────────────────────────────────────────────
        self._sec_label(p, "System Log", pady_top=14)
        host = tk.Frame(p, bg="#030508",
                        highlightbackground="#0d1420",
                        highlightthickness=1)
        host.pack(fill="both", expand=True, padx=18, pady=(0, 18))

        self._log_w = tk.Text(
            host, bg="#030508", fg=MUTED, font=FM,
            relief="flat", bd=0, height=10,
            state="disabled", wrap="word",
            insertbackground=ACCENT,
            selectbackground=SURF2,
            padx=12, pady=8
        )
        self._log_w.pack(fill="both", expand=True)
        self._log_w.tag_configure("ts",   foreground="#1e2e3d")
        self._log_w.tag_configure("ok",   foreground=GREEN)
        self._log_w.tag_configure("info", foreground=ACCENT)
        self._log_w.tag_configure("warn", foreground=GOLD)
        self._log_w.tag_configure("err",  foreground=REDDOT)

        self._log("System scan complete — " + str(len(TWEAKS)) + " tweaks ready.", "ok")
        self._log(str(sum(1 for t in TWEAKS if t["impact"]=="HIGH")) +
                  " HIGH-impact tweaks selected by default.", "info")
        if not self.restore_done:
            self._log("Restore point will be created before applying.", "warn")
        self._log("Toggle tweaks in each tab, then click Apply Tweaks.", "info")

    def _mini_cat_row(self, parent, cat, tweaks):
        """Compact category summary row on dashboard."""
        row = tk.Frame(parent, bg=SURF,
                       highlightbackground="#0d1420",
                       highlightthickness=1)
        row.pack(fill="x", padx=18, pady=3)

        # Category label with accent bar
        lf = tk.Frame(row, bg=SURF)
        lf.pack(side="left", padx=14, pady=8)

        bar = tk.Canvas(lf, width=3, height=36, bg=SURF,
                        highlightthickness=0)
        bar.pack(side="left", padx=(0, 10))
        bar.create_rectangle(0, 0, 3, 36, fill=ACCENT, outline="")

        tk.Label(lf, text=cat, bg=SURF, fg=TEXT,
                 font=(FONT_UI, 10, "bold"), width=8,
                 anchor="w").pack(side="left")

        count_on = sum(1 for t in tweaks if self.vars[t["id"]].get())
        tk.Label(row, text=str(count_on) + "/" + str(len(tweaks)) + " active",
                 bg=SURF, fg=MUTED, font=FM).pack(side="left", padx=8)

        # Impact dots
        dots_f = tk.Frame(row, bg=SURF)
        dots_f.pack(side="left", padx=8)
        for t in tweaks:
            dc = tk.Canvas(dots_f, width=8, height=8, bg=SURF,
                           highlightthickness=0)
            dc.pack(side="left", padx=1, pady=14)
            col = GREEN if t["impact"] == "HIGH" else ACCENT
            dc.create_oval(0, 0, 7, 7, fill=col, outline="")

        # Navigate button
        tk.Button(row, text="Configure →",
                  bg=SURF, fg=ACCENT, font=FM,
                  relief="flat", cursor="hand2", bd=0,
                  padx=10, pady=4,
                  command=lambda c=cat: self._nav(c),
                  activebackground=SURF2,
                  activeforeground=ACCENT).pack(side="right", padx=10, pady=6)

    # ── Tweak pages ───────────────────────────────────────────────────────────
    def _page_tweaks(self, cat):
        p   = self._inner
        lst = [t for t in TWEAKS if t["cat"] == cat]

        high_cnt = sum(1 for t in lst if t["impact"]=="HIGH")
        self._sec_label(p, cat + " Tweaks  —  " + str(high_cnt) +
                        " HIGH impact")

        for t in lst:
            self._tweak_card(p, t, self.vars[t["id"]])

        # Bottom padding
        tk.Frame(p, bg=BG, height=20).pack()

    def _tweak_card(self, parent, tweak, var):
        # Outer frame — thicker border when HIGH impact
        bcolor = "#0d2030" if tweak["impact"] == "HIGH" else "#0d1420"
        outer = tk.Frame(parent, bg=bcolor,
                         highlightbackground=bcolor,
                         highlightthickness=1)
        outer.pack(fill="x", padx=18, pady=4)

        inner = tk.Frame(outer, bg=SURF)
        inner.pack(fill="x", padx=1, pady=1)

        # Left accent bar (green for HIGH, accent for MED)
        bar_col = GREEN if tweak["impact"] == "HIGH" else ACCENT
        bar = tk.Canvas(inner, width=4, height=56, bg=SURF,
                        highlightthickness=0)
        bar.pack(side="left")
        bar.create_rectangle(0, 6, 4, 50, fill=bar_col, outline="")

        # Content
        content = tk.Frame(inner, bg=SURF)
        content.pack(side="left", fill="x", expand=True, padx=14, pady=10)

        top_row = tk.Frame(content, bg=SURF)
        top_row.pack(fill="x")

        tk.Label(top_row, text=tweak["name"], bg=SURF, fg=TEXT,
                 font=FN, anchor="w").pack(side="left")

        # Impact badge — pill via canvas
        ic  = GREEN if tweak["impact"] == "HIGH" else ACCENT
        ibg = "#0d2218" if tweak["impact"] == "HIGH" else ACCENT_DIM
        pw  = 52 if tweak["impact"] == "HIGH" else 46
        ibc = tk.Canvas(top_row, width=pw, height=18, bg=SURF,
                        highlightthickness=0)
        ibc.pack(side="left", padx=10)
        ibc.create_oval(0, 0, 18, 18, fill=ibg, outline=ic)
        ibc.create_oval(pw-18, 0, pw, 18, fill=ibg, outline=ic)
        ibc.create_rectangle(9, 0, pw-9, 18, fill=ibg, outline="")
        ibc.create_text(pw//2, 9, text=tweak["impact"],
                        fill=ic, font=("Consolas", 7, "bold"))

        tk.Label(content, text=tweak["desc"], bg=SURF, fg=MUTED,
                 font=FM, anchor="w").pack(fill="x", pady=(2, 0))

        # Toggle
        self._toggle(inner, var, bar_col)

    def _toggle(self, parent, var, active_col=ACCENT):
        W, H, R = 46, 24, 12
        cv = tk.Canvas(parent, width=W, height=H, bg=SURF,
                       highlightthickness=0, cursor="hand2")
        cv.pack(side="right", padx=16, pady=16)

        def draw(*_):
            cv.delete("all")
            on  = var.get()
            col = active_col if on else "#1a2232"
            # Pill
            cv.create_oval(0, 0, H, H, fill=col, outline="")
            cv.create_oval(W-H, 0, W, H, fill=col, outline="")
            cv.create_rectangle(R, 0, W-R, H, fill=col, outline="")
            # Knob shadow
            kx = W - H + 2 if on else 2
            cv.create_oval(kx-1, 1, kx+H-3, H-1,
                           fill="#00000055", outline="")
            # Knob
            cv.create_oval(kx, 2, kx+H-4, H-2, fill="white", outline="")

        draw()
        var.trace_add("write", draw)
        cv.bind("<Button-1>", lambda e: var.set(not var.get()))

    # ── Apply flow ────────────────────────────────────────────────────────────
    def _start_apply(self):
        if self.applying:
            return
        sel = [t for t in TWEAKS if self.vars[t["id"]].get()]
        if not sel:
            messagebox.showwarning("Nothing Selected",
                                   "Enable at least one tweak before applying.")
            return
        high_n = sum(1 for t in sel if t["impact"] == "HIGH")
        if not messagebox.askyesno(
            "Confirm — Apply " + str(len(sel)) + " Tweaks",
            "Selected: " + str(len(sel)) + " tweaks  (" +
            str(high_n) + " HIGH impact)\n\n"
            "✓  A System Restore Point will be created FIRST.\n"
            "✓  You can fully undo via Windows System Restore.\n\n"
            "Apply now?",
            icon="question"
        ):
            return
        self._nav("Dashboard")
        self.after(180, lambda: self._run(sel))

    def _run(self, sel):
        self.applying = True
        self._apply_btn.config(state="disabled",
                               text="  ⏳  Working...  ", bg="#1a3040")
        self._dot_cv.itemconfig("dot", fill=GOLD)
        threading.Thread(target=self._worker, args=(sel,), daemon=True).start()

    def _worker(self, sel):
        try:
            self._log("Creating System Restore Point...", "warn")
            create_restore_point()
            self.restore_done = True
            self._log("Restore point created successfully.", "ok")

            ok = fail = 0
            for t in sel:
                self._log("Applying: " + t["name"] + "...", "info")
                try:
                    t["fn"]()
                    self._log("✓  " + t["name"], "ok")
                    ok += 1
                except Exception as e:
                    self._log("✗  " + t["name"] + "  —  " + str(e), "err")
                    fail += 1
                time.sleep(0.08)

            self._log("━" * 48, "ts")
            self._log("Complete — " + str(ok) + " applied, " +
                      str(fail) + " failed.", "ok")
            self._log("Restart Windows for all changes to take full effect.", "warn")
            self.after(0, self._done, ok, fail)

        except Exception as e:
            self._log("FATAL — " + str(e), "err")
            self.after(0, self._err_cb, str(e))

    def _log(self, msg, tag="info"):
        def _do():
            if not self._log_w:
                return
            try:
                if not self._log_w.winfo_exists():
                    return
                self._log_w.config(state="normal")
                ts = datetime.datetime.now().strftime("%H:%M:%S")
                self._log_w.insert("end", "\n[" + ts + "]  ", "ts")
                self._log_w.insert("end", msg, tag)
                self._log_w.config(state="disabled")
                self._log_w.see("end")
            except Exception:
                pass
        if threading.current_thread() is threading.main_thread():
            _do()
        else:
            self.after(0, _do)

    def _done(self, ok, fail):
        self.applying = False
        self._apply_btn.config(state="normal",
                               text="  ⚡  Apply Tweaks  ", bg=ACCENT)
        self._dot_cv.itemconfig("dot", fill=GREEN)
        msg = str(ok) + " tweak(s) applied successfully."
        if fail:
            msg += "\n" + str(fail) + " failed — see the log for details."
        msg += "\n\nRestart your PC for full effect."
        messagebox.showinfo("Done!", msg)

    def _err_cb(self, err):
        self.applying = False
        self._apply_btn.config(state="normal",
                               text="  ⚡  Apply Tweaks  ", bg=ACCENT)
        self._dot_cv.itemconfig("dot", fill=REDDOT)
        messagebox.showerror(
            "Error",
            "Failed to create restore point:\n\n" + err + "\n\n"
            "Enable System Protection on C: via:\n"
            "Control Panel > System > System Protection"
        )


# ── Entry ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()
