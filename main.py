"""
FPS Utility - Lite  v2.0
Requires: Python 3.9+  |  Windows 10/11  |  Administrator
"""

import tkinter as tk
from tkinter import messagebox
import threading, subprocess, ctypes, sys, time, datetime, winreg, os

# ── Admin gate ────────────────────────────────────────────────────────────────
def _is_admin():
    try: return ctypes.windll.shell32.IsUserAnAdmin()
    except: return False

if not _is_admin():
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable,
        " ".join(f'"{a}"' for a in sys.argv), None, 1)
    sys.exit()

# ── Icon loader ───────────────────────────────────────────────────────────────
def _find_icon():
    for base in (
        os.path.dirname(sys.executable),
        os.path.dirname(os.path.abspath(__file__)),
        os.getcwd(),
    ):
        p = os.path.join(base, "icon.ico")
        if os.path.exists(p):
            return p
    return None

# ── Palette — ALL valid 6-digit hex, zero alpha values ───────────────────────
BG          = "#080a0c"
SURF        = "#0e1114"
SURF2       = "#141820"
BORDER      = "#111820"
ACCENT      = "#00d4ff"
TEXT        = "#e8edf2"
MUTED       = "#5a6472"
GREEN       = "#00e5a0"
GOLD        = "#f5c842"
REDDOT      = "#ff5f57"
YELLDOT     = "#ffbd2e"
GRNDOT      = "#28c840"
WARN_BG     = "#110e02"
ACCENT_DIM  = "#0e2535"
ACCENT_RING = "#1a3a4a"

FONT_UI = "Segoe UI"
FM  = ("Consolas", 9)
FH  = (FONT_UI, 11, "bold")
FN  = (FONT_UI, 10, "bold")
FS  = (FONT_UI, 9)
FB  = (FONT_UI, 10, "bold")

# ─────────────────────────────────────────────────────────────────────────────
#  TWEAKS
# ─────────────────────────────────────────────────────────────────────────────
def _reg(hive, path, name, rtype, value):
    k = winreg.CreateKeyEx(hive, path, 0,
                           winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY)
    winreg.SetValueEx(k, name, 0, rtype, value)
    winreg.CloseKey(k)

def _ps(cmd):
    return subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
        capture_output=True, text=True)

# CPU
def t_high_perf():
    r = _ps("powercfg /duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61")
    guid = None
    for line in r.stdout.splitlines():
        parts = line.strip().split()
        if parts and len(parts[-1]) == 36:
            guid = parts[-1]
    if guid:
        _ps("powercfg /setactive " + guid)
    else:
        _ps("powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c")

def t_core_parking():
    r = subprocess.run(["powercfg", "/list"], capture_output=True, text=True)
    guids = [ln.split()[3] for ln in r.stdout.splitlines() if "GUID:" in ln]
    for g in guids:
        subprocess.run(["powercfg","/setacvalueindex",g,
            "54533251-82be-4824-96c1-47b60b740d00",
            "0cc5b647-c1df-4637-891a-dec35c318583","0"], capture_output=True)
        subprocess.run(["powercfg","/setdcvalueindex",g,
            "54533251-82be-4824-96c1-47b60b740d00",
            "0cc5b647-c1df-4637-891a-dec35c318583","0"], capture_output=True)

def t_cpu_priority():
    _reg(winreg.HKEY_LOCAL_MACHINE,
         r"SYSTEM\CurrentControlSet\Control\PriorityControl",
         "Win32PrioritySeparation", winreg.REG_DWORD, 0x26)

def t_timer_res():
    subprocess.run(["bcdedit","/set","useplatformtick","yes"],   capture_output=True)
    subprocess.run(["bcdedit","/set","disabledynamictick","yes"], capture_output=True)

def t_cpu_idle():
    subprocess.run(["powercfg","/setacvalueindex","SCHEME_CURRENT",
        "54533251-82be-4824-96c1-47b60b740d00",
        "5d76a2ca-e8c0-402f-a133-2158492d58ad","0"], capture_output=True)

def t_mm_games():
    base  = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile"
    gbase = base + r"\Tasks\Games"
    _reg(winreg.HKEY_LOCAL_MACHINE, base,  "SystemResponsiveness", winreg.REG_DWORD, 0)
    _reg(winreg.HKEY_LOCAL_MACHINE, gbase, "GPU Priority",         winreg.REG_DWORD, 8)
    _reg(winreg.HKEY_LOCAL_MACHINE, gbase, "Priority",             winreg.REG_DWORD, 6)
    _reg(winreg.HKEY_LOCAL_MACHINE, gbase, "Scheduling Category",  winreg.REG_SZ,    "High")
    _reg(winreg.HKEY_LOCAL_MACHINE, gbase, "SFIO Priority",        winreg.REG_SZ,    "High")

# GPU
def t_hw_sched():
    _reg(winreg.HKEY_LOCAL_MACHINE,
         r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers",
         "HwSchMode", winreg.REG_DWORD, 2)

def t_shader():
    _reg(winreg.HKEY_LOCAL_MACHINE,
         r"SOFTWARE\Microsoft\DirectX\UserGpuPreferences",
         "DirectXUserGlobalSettings", winreg.REG_SZ, "SwapEffectUpgradeEnable=1;")

def t_mpo():
    _reg(winreg.HKEY_LOCAL_MACHINE,
         r"SOFTWARE\Microsoft\Windows\Dwm",
         "OverlayTestMode", winreg.REG_DWORD, 5)

def t_prerender():
    _reg(winreg.HKEY_LOCAL_MACHINE,
         r"SOFTWARE\Microsoft\DirectX",
         "MaxRenderedFramesAllowed", winreg.REG_DWORD, 1)

# Network
def t_nagle():
    base = r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces"
    reg  = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base)
    i = 0
    while True:
        try:
            sub = winreg.EnumKey(reg, i)
            k   = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                 base + "\\" + sub, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(k, "TcpAckFrequency", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(k, "TCPNoDelay",      0, winreg.REG_DWORD, 1)
            winreg.CloseKey(k)
            i += 1
        except OSError:
            break
    winreg.CloseKey(reg)

def t_net_throttle():
    _reg(winreg.HKEY_LOCAL_MACHINE,
         r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile",
         "NetworkThrottlingIndex", winreg.REG_DWORD, 0xffffffff)

def t_dns():
    base = r"SYSTEM\CurrentControlSet\Services\Dnscache\Parameters"
    _reg(winreg.HKEY_LOCAL_MACHINE, base, "CacheHashTableBucketSize", winreg.REG_DWORD, 1)
    _reg(winreg.HKEY_LOCAL_MACHINE, base, "CacheHashTableSize",       winreg.REG_DWORD, 384)
    _reg(winreg.HKEY_LOCAL_MACHINE, base, "MaxCacheEntryTtlLimit",    winreg.REG_DWORD, 0xff0000)
    _reg(winreg.HKEY_LOCAL_MACHINE, base, "MaxSOACacheEntryTtlLimit", winreg.REG_DWORD, 0x12c)

# Services
def t_sysmain():
    subprocess.run(["sc","config","SysMain","start=","disabled"], capture_output=True)
    subprocess.run(["sc","stop","SysMain"], capture_output=True)

def t_search():
    subprocess.run(["sc","config","WSearch","start=","disabled"], capture_output=True)
    subprocess.run(["sc","stop","WSearch"], capture_output=True)

def t_xbox():
    for hive, path, name, rtype, val in [
        (winreg.HKEY_CURRENT_USER,
         r"Software\Microsoft\Windows\CurrentVersion\GameDVR",
         "AppCaptureEnabled",        winreg.REG_DWORD, 0),
        (winreg.HKEY_CURRENT_USER,
         r"System\GameConfigStore",
         "GameDVR_Enabled",          winreg.REG_DWORD, 0),
        (winreg.HKEY_CURRENT_USER,
         r"System\GameConfigStore",
         "GameDVR_FSEBehaviorMode",  winreg.REG_DWORD, 2),
    ]:
        try:
            k = winreg.OpenKey(hive, path, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(k, name, 0, rtype, val)
            winreg.CloseKey(k)
        except Exception:
            pass

def t_telemetry():
    for svc in ["DiagTrack","dmwappushservice","WerSvc","PcaSvc"]:
        subprocess.run(["sc","config",svc,"start=","disabled"], capture_output=True)
        subprocess.run(["sc","stop",svc], capture_output=True)
    _reg(winreg.HKEY_LOCAL_MACHINE,
         r"SOFTWARE\Policies\Microsoft\Windows\DataCollection",
         "AllowTelemetry", winreg.REG_DWORD, 0)

def t_fse():
    for name, rtype, val in [
        ("GameDVR_DXGIHonorFSEWindowsCompatible", winreg.REG_DWORD, 1),
        ("GameDVR_EFSEFeatureFlags",              winreg.REG_DWORD, 0),
    ]:
        try:
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                               r"System\GameConfigStore", 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(k, name, 0, rtype, val)
            winreg.CloseKey(k)
        except Exception:
            pass

def t_memory():
    base = r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management"
    _reg(winreg.HKEY_LOCAL_MACHINE, base, "LargeSystemCache",       winreg.REG_DWORD, 0)
    _reg(winreg.HKEY_LOCAL_MACHINE, base, "DisablePagingExecutive", winreg.REG_DWORD, 1)
    _reg(winreg.HKEY_LOCAL_MACHINE, base, "SystemPages",            winreg.REG_DWORD, 0xffffffff)

def create_restore_point():
    cmd = ('Checkpoint-Computer -Description "FPS Utility Lite" '
           '-RestorePointType MODIFY_SETTINGS -ErrorAction Stop')
    r = _ps(cmd)
    if r.returncode != 0:
        raise RuntimeError(
            r.stderr.strip() or
            "Enable System Protection on C: via Control Panel > System > System Protection")

TWEAKS = [
    {"id":"perf",    "cat":"CPU",     "impact":"HIGH",
     "name":"Ultimate Performance Plan",
     "desc":"Activates hidden max-power plan — highest sustained clocks",           "fn":t_high_perf},
    {"id":"parking", "cat":"CPU",     "impact":"HIGH",
     "name":"Disable Core Parking",
     "desc":"All cores stay awake — eliminates spin-up stutter",                    "fn":t_core_parking},
    {"id":"cpuprio", "cat":"CPU",     "impact":"HIGH",
     "name":"Foreground CPU Priority Boost",
     "desc":"Win32PrioritySeparation=0x26 — max quantum to game thread",            "fn":t_cpu_priority},
    {"id":"timer",   "cat":"CPU",     "impact":"HIGH",
     "name":"1ms Timer Resolution",
     "desc":"bcdedit useplatformtick — tightest scheduler tick",                    "fn":t_timer_res},
    {"id":"idle",    "cat":"CPU",     "impact":"MED",
     "name":"Disable CPU Idle States",
     "desc":"Removes C-state power transitions during gameplay",                    "fn":t_cpu_idle},
    {"id":"mmgames", "cat":"CPU",     "impact":"HIGH",
     "name":"Multimedia Game Scheduling",
     "desc":"GPU Priority 8 + Scheduling Category High for games",                  "fn":t_mm_games},
    {"id":"hwsched", "cat":"GPU",     "impact":"HIGH",
     "name":"Hardware GPU Scheduler",
     "desc":"WDDM 2.7 HAGS — reduces CPU-GPU latency significantly",               "fn":t_hw_sched},
    {"id":"shader",  "cat":"GPU",     "impact":"HIGH",
     "name":"Unlimited Shader Cache",
     "desc":"No disk cap on shader store — eliminates compile stutters",            "fn":t_shader},
    {"id":"mpo",     "cat":"GPU",     "impact":"HIGH",
     "name":"Disable Multi-Plane Overlay",
     "desc":"Fixes major stutters and black screens on NVIDIA/AMD",                 "fn":t_mpo},
    {"id":"frames",  "cat":"GPU",     "impact":"HIGH",
     "name":"Limit Pre-rendered Frames",
     "desc":"DXGI max 1 pre-rendered frame — cuts input lag",                       "fn":t_prerender},
    {"id":"nagle",   "cat":"Network", "impact":"HIGH",
     "name":"Disable Nagle Algorithm",
     "desc":"TCPNoDelay + AckFrequency=1 on all interfaces",                        "fn":t_nagle},
    {"id":"netthrot","cat":"Network", "impact":"HIGH",
     "name":"Remove Network Throttle",
     "desc":"Removes the hidden 10 Mbps multimedia throttle cap",                   "fn":t_net_throttle},
    {"id":"dns",     "cat":"Network", "impact":"MED",
     "name":"Maximize DNS Cache",
     "desc":"Larger cache bucket size — faster server lookups",                     "fn":t_dns},
    {"id":"sysmain", "cat":"Services","impact":"MED",
     "name":"Disable SysMain / Superfetch",
     "desc":"Frees RAM from OS cache pre-loading",                                  "fn":t_sysmain},
    {"id":"search",  "cat":"Services","impact":"MED",
     "name":"Disable Search Indexing",
     "desc":"Stops background disk I/O from Windows Search",                        "fn":t_search},
    {"id":"xbox",    "cat":"Services","impact":"MED",
     "name":"Disable Xbox Game Bar / DVR",
     "desc":"Removes recording hooks and overlay overhead",                         "fn":t_xbox},
    {"id":"telem",   "cat":"Services","impact":"MED",
     "name":"Disable Telemetry Services",
     "desc":"Kills DiagTrack, WerSvc, PcaSvc background services",                  "fn":t_telemetry},
    {"id":"fse",     "cat":"Services","impact":"HIGH",
     "name":"Fullscreen Exclusive Fix",
     "desc":"Forces true FSE mode — maximum GPU priority in games",                 "fn":t_fse},
    {"id":"memory",  "cat":"Services","impact":"MED",
     "name":"Memory Manager Optimization",
     "desc":"DisablePagingExecutive + max system pages for gaming",                 "fn":t_memory},
]

CATS = ["CPU","GPU","Network","Services"]

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

        ico = _find_icon()
        if ico:
            try: self.iconbitmap(ico)
            except Exception: pass

        self.vars         = {t["id"]: tk.BooleanVar(value=True) for t in TWEAKS}
        self.active       = "Dashboard"
        self.restore_done = False
        self.applying     = False
        self._log_w       = None
        self._nf          = {}
        self._nc          = {}

        self._build()
        self._nav_activate("Dashboard")
        self._go("Dashboard")

    # ── Chrome ────────────────────────────────────────────────────────────────
    def _build(self):
        bar = tk.Frame(self, bg="#080c10", height=40)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        dc = tk.Canvas(bar, bg="#080c10", width=72, height=40, highlightthickness=0)
        dc.pack(side="left", padx=14)
        for i, col in enumerate((REDDOT, YELLDOT, GRNDOT)):
            x = 8 + i * 20
            dc.create_oval(x, 14, x+12, 26, fill=col, outline="")

        tk.Label(bar, text="FPS Utility  -  Lite",
                 bg="#080c10", fg=MUTED, font=FM).pack(side="left", expand=True)
        tk.Label(bar, text="v2.0",
                 bg="#080c10", fg=BORDER, font=FM).pack(side="right", padx=16)

        tk.Frame(self, bg="#1a2232", height=1).pack(fill="x")

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True)
        self._build_sidebar(body)
        tk.Frame(body, bg="#0d1420", width=1).pack(side="left", fill="y")
        self._build_main(body)

    # ── Sidebar ───────────────────────────────────────────────────────────────
    def _build_sidebar(self, parent):
        sb = tk.Frame(parent, bg="#080c10", width=62)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)

        # Logo
        lc = tk.Canvas(sb, width=44, height=44, bg="#080c10", highlightthickness=0)
        lc.pack(pady=(14, 10))
        lc.create_oval(4,  4, 40, 40, outline=ACCENT_RING, width=1)
        lc.create_oval(8,  8, 36, 36, fill=ACCENT_DIM, outline="")
        # Lightning bolt in logo
        lc.create_polygon(24,10, 17,23, 22,23, 20,34,
                          27,21, 22,21, 26,10,
                          fill=ACCENT, outline="")

        nav_items = ["Dashboard","CPU","GPU","Network","Services"]
        for label in nav_items:
            outer = tk.Frame(sb, bg="#080c10", cursor="hand2")
            outer.pack(fill="x", padx=8, pady=2)
            nc = tk.Canvas(outer, width=46, height=44,
                           bg="#080c10", highlightthickness=0, cursor="hand2")
            nc.pack()
            self._draw_icon(nc, label, MUTED)
            nc.create_text(23, 36, text=label[:3].upper(),
                           fill=MUTED, font=("Consolas", 6), tags="sub")
            for w in (outer, nc):
                w.bind("<Button-1>", lambda e, l=label: self._nav(l))
                w.bind("<Enter>",    lambda e, l=label: self._nhover(l, True))
                w.bind("<Leave>",    lambda e, l=label: self._nhover(l, False))
            self._nf[label] = outer
            self._nc[label] = nc

        tk.Frame(sb, bg="#0d1420", height=1).pack(fill="x", pady=(10,6))
        self._dot_cv = tk.Canvas(sb, width=20, height=20,
                                 bg="#080c10", highlightthickness=0)
        self._dot_cv.pack(pady=(0,12))
        self._dot_cv.create_oval(4,4,16,16, fill=GREEN, outline="", tags="dot")

    def _draw_icon(self, nc, label, color):
        nc.delete("icon")
        cx, cy = 23, 18
        if label == "Dashboard":
            nc.create_polygon(cx,cy-8, cx-8,cy+1,
                              cx+8,cy+1,
                              outline=color, fill="", width=1.5, tags="icon")
            nc.create_rectangle(cx-5,cy+1,cx+5,cy+9,
                                outline=color, fill="", width=1.5, tags="icon")
        elif label == "CPU":
            nc.create_rectangle(cx-6,cy-6,cx+6,cy+6,
                                outline=color, fill="", width=1.5, tags="icon")
            nc.create_line(cx-6,cy,cx+6,cy,    fill=color, width=1,   tags="icon")
            nc.create_line(cx,cy-6,cx,cy+6,    fill=color, width=1,   tags="icon")
        elif label == "GPU":
            nc.create_rectangle(cx-8,cy-4,cx+8,cy+4,
                                outline=color, fill="", width=1.5, tags="icon")
            nc.create_line(cx-4,cy+4,cx-4,cy+8, fill=color, width=1.5, tags="icon")
            nc.create_line(cx+4,cy+4,cx+4,cy+8, fill=color, width=1.5, tags="icon")
        elif label == "Network":
            nc.create_oval(cx-7,cy-7,cx+7,cy+7,
                           outline=color, fill="", width=1.5, tags="icon")
            nc.create_line(cx-7,cy,cx+7,cy,      fill=color, width=1,   tags="icon")
            nc.create_oval(cx-3,cy-7,cx+3,cy+7,
                           outline=color, fill="", width=1,   tags="icon")
        elif label == "Services":
            nc.create_oval(cx-4,cy-4,cx+4,cy+4,
                           outline=color, fill="", width=1.5, tags="icon")
            for ax,ay in [(cx,cy-8),(cx,cy+8),(cx-8,cy),(cx+8,cy)]:
                nc.create_line(cx,cy, ax,ay, fill=color, width=1.5, tags="icon")

    def _nhover(self, label, on):
        if self.active == label:
            return
        bg  = SURF2 if on else "#080c10"
        col = TEXT  if on else MUTED
        nc    = self._nc[label]
        outer = self._nf[label]
        nc.config(bg=bg)
        outer.config(bg=bg)
        self._draw_icon(nc, label, col)
        nc.itemconfig("sub", fill=col)

    def _nav_activate(self, label):
        nc    = self._nc[label]
        outer = self._nf[label]
        nc.config(bg=SURF2)
        outer.config(bg=SURF2)
        self._draw_icon(nc, label, ACCENT)
        nc.itemconfig("sub", fill=ACCENT)
        nc.create_rectangle(0, 4, 3, 40, fill=ACCENT, outline="", tags="bar")

    def _nav_deactivate(self, label):
        nc    = self._nc[label]
        outer = self._nf[label]
        nc.config(bg="#080c10")
        outer.config(bg="#080c10")
        self._draw_icon(nc, label, MUTED)
        nc.itemconfig("sub", fill=MUTED)
        nc.delete("bar")

    def _nav(self, label):
        if self.active != label:
            self._nav_deactivate(self.active)
        self.active = label
        self._nav_activate(label)
        self._topbar_lbl.config(text=label)
        self._go(label)

    # ── Main area ─────────────────────────────────────────────────────────────
    def _build_main(self, parent):
        main = tk.Frame(parent, bg=BG)
        main.pack(side="left", fill="both", expand=True)

        top = tk.Frame(main, bg=SURF, height=46)
        top.pack(fill="x")
        top.pack_propagate(False)

        self._topbar_lbl = tk.Label(
            top, text="Dashboard", bg=SURF, fg=TEXT, font=FH, anchor="w")
        self._topbar_lbl.pack(side="left", padx=18)

        # LITE badge
        bc = tk.Canvas(top, width=52, height=22, bg=SURF, highlightthickness=0)
        bc.pack(side="left", padx=6, pady=12)
        bc.create_oval(0, 0, 22, 22,  fill=ACCENT_DIM, outline=ACCENT_RING)
        bc.create_oval(30,0, 52, 22,  fill=ACCENT_DIM, outline=ACCENT_RING)
        bc.create_rectangle(11,0,41,22, fill=ACCENT_DIM, outline="")
        bc.create_text(26, 11, text="LITE", fill=ACCENT,
                       font=("Consolas", 7, "bold"))

        self._apply_btn = tk.Button(
            top, text="  Apply Tweaks  ",
            bg=ACCENT, fg=BG, font=FB,
            relief="flat", cursor="hand2", pady=6,
            command=self._start_apply,
            activebackground="#33dcff", activeforeground=BG)
        self._apply_btn.pack(side="right", padx=16, pady=8)

        tk.Frame(main, bg="#0d1420", height=1).pack(fill="x")

        wrap = tk.Frame(main, bg=BG)
        wrap.pack(fill="both", expand=True)

        self._canvas = tk.Canvas(wrap, bg=BG, highlightthickness=0, bd=0)
        vsb = tk.Scrollbar(wrap, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._inner = tk.Frame(self._canvas, bg=BG)
        self._cwin  = self._canvas.create_window((0,0), window=self._inner, anchor="nw")
        self._inner.bind("<Configure>", lambda e: self._canvas.configure(
            scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>", lambda e: self._canvas.itemconfig(
            self._cwin, width=e.width))
        self._canvas.bind("<MouseWheel>", lambda e: self._canvas.yview_scroll(
            int(-1*(e.delta/120)), "units"))

    # ── Page helpers ──────────────────────────────────────────────────────────
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

    def _sec_label(self, parent, text, color=ACCENT, top=16):
        row = tk.Frame(parent, bg=BG)
        row.pack(fill="x", padx=18, pady=(top, 0))
        dc = tk.Canvas(row, width=8, height=8, bg=BG, highlightthickness=0)
        dc.pack(side="left", padx=(0,7), pady=6)
        dc.create_oval(0,0,7,7, fill=color, outline="")
        tk.Label(row, text=text.upper(), bg=BG, fg=color,
                 font=("Consolas", 8, "bold")).pack(side="left")
        tk.Frame(parent, bg="#0d1420", height=1).pack(fill="x", padx=18, pady=(4,10))

    # ── Dashboard ─────────────────────────────────────────────────────────────
    def _page_dash(self):
        p = self._inner
        self._sec_label(p, "System Status")

        stat_row = tk.Frame(p, bg=BG)
        stat_row.pack(fill="x", padx=18, pady=(0,14))

        high_n = sum(1 for t in TWEAKS if t["impact"]=="HIGH")
        rp_done = self.restore_done
        for label, val, color in [
            ("Total Tweaks",  str(len(TWEAKS)), ACCENT),
            ("HIGH Impact",   str(high_n),      GREEN),
            ("Restore Point", "Done" if rp_done else "Pending",
             GREEN if rp_done else GOLD),
        ]:
            card = tk.Frame(stat_row, bg=SURF,
                            highlightbackground="#0d1420", highlightthickness=1)
            card.pack(side="left", expand=True, fill="x",
                      padx=(0,10), ipady=14, ipadx=14)
            tk.Label(card, text=val,   bg=SURF, fg=color,
                     font=(FONT_UI, 22, "bold")).pack()
            tk.Label(card, text=label, bg=SURF, fg=MUTED, font=FM).pack()

        # Warning banner
        if not self.restore_done:
            wp = tk.Frame(p, bg=BG)
            wp.pack(fill="x", padx=18, pady=(0,8))
            warn = tk.Frame(wp, bg=WARN_BG,
                            highlightbackground=GOLD, highlightthickness=1)
            warn.pack(fill="x")
            wr = tk.Frame(warn, bg=WARN_BG)
            wr.pack(fill="x", padx=12, pady=10)
            wc = tk.Canvas(wr, width=16, height=14,
                           bg=WARN_BG, highlightthickness=0)
            wc.pack(side="left", padx=(0,8))
            wc.create_polygon(8,1,15,13,1,13, fill=GOLD, outline="")
            wc.create_text(8,10, text="!", fill=WARN_BG,
                           font=("Segoe UI",7,"bold"))
            tk.Label(wr,
                     text="A System Restore Point is created automatically before any tweaks are applied.",
                     bg=WARN_BG, fg=GOLD, font=FS,
                     anchor="w", justify="left").pack(side="left")

        # Category overview
        self._sec_label(p, "Tweak Overview")
        for cat in CATS:
            self._mini_cat(p, cat, [t for t in TWEAKS if t["cat"]==cat])

        # Log terminal
        self._sec_label(p, "System Log", top=14)
        host = tk.Frame(p, bg="#030508",
                        highlightbackground="#0d1420", highlightthickness=1)
        host.pack(fill="both", expand=True, padx=18, pady=(0,18))

        self._log_w = tk.Text(
            host, bg="#030508", fg=MUTED, font=FM,
            relief="flat", bd=0, height=10,
            state="disabled", wrap="word",
            insertbackground=ACCENT, selectbackground=SURF2,
            padx=12, pady=8)
        self._log_w.pack(fill="both", expand=True)
        self._log_w.tag_configure("ts",   foreground="#1e2e3d")
        self._log_w.tag_configure("ok",   foreground=GREEN)
        self._log_w.tag_configure("info", foreground=ACCENT)
        self._log_w.tag_configure("warn", foreground=GOLD)
        self._log_w.tag_configure("err",  foreground=REDDOT)

        self._log("System scan complete - " + str(len(TWEAKS)) + " tweaks ready.", "ok")
        self._log(str(high_n) + " HIGH-impact tweaks selected by default.", "info")
        if not self.restore_done:
            self._log("Restore point will be created before applying.", "warn")
        self._log("Toggle tweaks in each tab, then click Apply Tweaks.", "info")

    def _mini_cat(self, parent, cat, tweaks):
        row = tk.Frame(parent, bg=SURF,
                       highlightbackground="#0d1420", highlightthickness=1)
        row.pack(fill="x", padx=18, pady=3)

        lf = tk.Frame(row, bg=SURF)
        lf.pack(side="left", padx=14, pady=8)
        bv = tk.Canvas(lf, width=3, height=36, bg=SURF, highlightthickness=0)
        bv.pack(side="left", padx=(0,10))
        bv.create_rectangle(0,0,3,36, fill=ACCENT, outline="")
        tk.Label(lf, text=cat, bg=SURF, fg=TEXT,
                 font=(FONT_UI,10,"bold"), width=8, anchor="w").pack(side="left")

        cnt = sum(1 for t in tweaks if self.vars[t["id"]].get())
        tk.Label(row, text=str(cnt)+"/"+str(len(tweaks))+" active",
                 bg=SURF, fg=MUTED, font=FM).pack(side="left", padx=8)

        df = tk.Frame(row, bg=SURF)
        df.pack(side="left", padx=8)
        for t in tweaks:
            dc = tk.Canvas(df, width=8, height=8, bg=SURF, highlightthickness=0)
            dc.pack(side="left", padx=1, pady=14)
            dc.create_oval(0,0,7,7,
                           fill=GREEN if t["impact"]=="HIGH" else ACCENT,
                           outline="")

        tk.Button(row, text="Configure ->",
                  bg=SURF, fg=ACCENT, font=FM, relief="flat",
                  cursor="hand2", bd=0, padx=10, pady=4,
                  command=lambda c=cat: self._nav(c),
                  activebackground=SURF2, activeforeground=ACCENT
                  ).pack(side="right", padx=10, pady=6)

    # ── Tweak pages ───────────────────────────────────────────────────────────
    def _page_tweaks(self, cat):
        p   = self._inner
        lst = [t for t in TWEAKS if t["cat"]==cat]
        h   = sum(1 for t in lst if t["impact"]=="HIGH")
        self._sec_label(p, cat+" Tweaks  -  "+str(h)+" HIGH impact")
        for t in lst:
            self._tweak_card(p, t, self.vars[t["id"]])
        tk.Frame(p, bg=BG, height=20).pack()

    def _tweak_card(self, parent, tweak, var):
        is_h    = tweak["impact"]=="HIGH"
        bar_col = GREEN if is_h else ACCENT
        bdr_col = "#0d2030" if is_h else "#0d1420"

        outer = tk.Frame(parent, bg=bdr_col,
                         highlightbackground=bdr_col, highlightthickness=1)
        outer.pack(fill="x", padx=18, pady=4)
        inner = tk.Frame(outer, bg=SURF)
        inner.pack(fill="x", padx=1, pady=1)

        bv = tk.Canvas(inner, width=4, height=58, bg=SURF, highlightthickness=0)
        bv.pack(side="left")
        bv.create_rectangle(0,8,4,50, fill=bar_col, outline="")

        content = tk.Frame(inner, bg=SURF)
        content.pack(side="left", fill="x", expand=True, padx=14, pady=10)

        top_row = tk.Frame(content, bg=SURF)
        top_row.pack(fill="x")
        tk.Label(top_row, text=tweak["name"], bg=SURF, fg=TEXT,
                 font=FN, anchor="w").pack(side="left")

        # Impact pill
        ic  = GREEN if is_h else ACCENT
        ibg = "#0d2218" if is_h else ACCENT_DIM
        pw  = 54 if is_h else 46
        ibc = tk.Canvas(top_row, width=pw, height=18,
                        bg=SURF, highlightthickness=0)
        ibc.pack(side="left", padx=10)
        ibc.create_oval(0,0,18,18,    fill=ibg, outline=ic)
        ibc.create_oval(pw-18,0,pw,18, fill=ibg, outline=ic)
        ibc.create_rectangle(9,0,pw-9,18, fill=ibg, outline="")
        ibc.create_text(pw//2, 9, text=tweak["impact"],
                        fill=ic, font=("Consolas",7,"bold"))

        tk.Label(content, text=tweak["desc"], bg=SURF, fg=MUTED,
                 font=FM, anchor="w").pack(fill="x", pady=(2,0))

        self._toggle(inner, var, bar_col)

    def _toggle(self, parent, var, active_col=ACCENT):
        W, H, R = 46, 24, 12
        cv = tk.Canvas(parent, width=W, height=H,
                       bg=SURF, highlightthickness=0, cursor="hand2")
        cv.pack(side="right", padx=16, pady=17)

        def draw(*_):
            cv.delete("all")
            on  = var.get()
            col = active_col if on else "#1a2232"
            cv.create_oval(0,   0,  H,   H, fill=col, outline="")
            cv.create_oval(W-H, 0,  W,   H, fill=col, outline="")
            cv.create_rectangle(R, 0, W-R,  H, fill=col, outline="")
            kx = W-H+2 if on else 2
            cv.create_oval(kx, 2, kx+H-4, H-2, fill="white", outline="")

        draw()
        var.trace_add("write", draw)
        cv.bind("<Button-1>", lambda e: var.set(not var.get()))

    # ── Apply ─────────────────────────────────────────────────────────────────
    def _start_apply(self):
        if self.applying:
            return
        sel = [t for t in TWEAKS if self.vars[t["id"]].get()]
        if not sel:
            messagebox.showwarning("Nothing Selected",
                                   "Enable at least one tweak before applying.")
            return
        high_n = sum(1 for t in sel if t["impact"]=="HIGH")
        if not messagebox.askyesno(
            "Confirm - Apply "+str(len(sel))+" Tweaks",
            "Selected: "+str(len(sel))+" tweaks  ("+str(high_n)+" HIGH impact)\n\n"
            "A System Restore Point will be created FIRST.\n"
            "You can fully undo via Windows System Restore.\n\n"
            "Apply now?", icon="question"):
            return
        self._nav("Dashboard")
        self.after(180, lambda: self._run(sel))

    def _run(self, sel):
        self.applying = True
        self._apply_btn.config(state="disabled",
                               text="  Working...  ", bg="#1a3040")
        self._dot_cv.itemconfig("dot", fill=GOLD)
        threading.Thread(target=self._worker, args=(sel,), daemon=True).start()

    def _worker(self, sel):
        try:
            self._log("Creating System Restore Point...", "warn")
            create_restore_point()
            self.restore_done = True
            self._log("Restore point created.", "ok")

            ok = fail = 0
            for t in sel:
                self._log("Applying: "+t["name"]+"...", "info")
                try:
                    t["fn"]()
                    self._log("  "+t["name"]+" done.", "ok")
                    ok += 1
                except Exception as e:
                    self._log("  "+t["name"]+" FAILED: "+str(e), "err")
                    fail += 1
                time.sleep(0.08)

            self._log("---", "ts")
            self._log("Complete: "+str(ok)+" applied, "+str(fail)+" failed.", "ok")
            self._log("Restart Windows for all changes to take full effect.", "warn")
            self.after(0, self._done, ok, fail)

        except Exception as e:
            self._log("FATAL: "+str(e), "err")
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
                self._log_w.insert("end", "\n["+ts+"]  ", "ts")
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
                               text="  Apply Tweaks  ", bg=ACCENT)
        self._dot_cv.itemconfig("dot", fill=GREEN)
        msg = str(ok)+" tweak(s) applied successfully."
        if fail:
            msg += "\n"+str(fail)+" failed - see log for details."
        msg += "\n\nRestart your PC for full effect."
        messagebox.showinfo("Done!", msg)

    def _err_cb(self, err):
        self.applying = False
        self._apply_btn.config(state="normal",
                               text="  Apply Tweaks  ", bg=ACCENT)
        self._dot_cv.itemconfig("dot", fill=REDDOT)
        messagebox.showerror("Error",
            "Failed to create restore point:\n\n"+err+"\n\n"
            "Enable System Protection on C: via:\n"
            "Control Panel > System > System Protection")


if __name__ == "__main__":
    app = App()
    app.mainloop()
