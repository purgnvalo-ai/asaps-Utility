"""
AURA - Precision Tuning Utility
Requires: Python 3.9+  |  Windows 10/11  |  Administrator
"""

import tkinter as tk
from tkinter import messagebox
import threading, subprocess, ctypes, sys, time, datetime, winreg, os

# ── Admin Gate ────────────────────────────────────────────────────────────────
def _is_admin():
    try: return ctypes.windll.shell32.IsUserAnAdmin()
    except: return False

if not _is_admin():
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable,
        " ".join(f'"{a}"' for a in sys.argv), None, 1)
    sys.exit()

# ── Palette & Fonts (Dark Luxury) ─────────────────────────────────────────────
BG          = "#030303"
SURF        = "#0a0a0a"
SURF2       = "#121212"
BORDER      = "#222222"
ACCENT      = "#D4AF37" # Gold
TEXT        = "#f5f5f5"
MUTED       = "#777777"

FONT_SANS   = ("Segoe UI", 10)
FONT_SERIF  = ("Georgia", 18)
FONT_SERIF_L= ("Georgia", 28)
FONT_MONO   = ("Consolas", 8)
FONT_MONO_B = ("Consolas", 8, "bold")

# ─────────────────────────────────────────────────────────────────────────────
#  TWEAKS (Functional)
# ─────────────────────────────────────────────────────────────────────────────
def _reg(hive, path, name, rtype, value):
    k = winreg.CreateKeyEx(hive, path, 0, winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY)
    winreg.SetValueEx(k, name, 0, rtype, value)
    winreg.CloseKey(k)

def _ps(cmd):
    return subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
                          capture_output=True, text=True)

# CPU
def t_high_perf():
    r = _ps("powercfg /duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61")
    guid = None
    for line in r.stdout.splitlines():
        parts = line.strip().split()
        if parts and len(parts[-1]) == 36:
            guid = parts[-1]
    if guid: _ps("powercfg /setactive " + guid)
    else: _ps("powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c")

def t_core_parking():
    r = subprocess.run(["powercfg", "/list"], capture_output=True, text=True)
    guids = [ln.split()[3] for ln in r.stdout.splitlines() if "GUID:" in ln]
    for g in guids:
        subprocess.run(["powercfg","/setacvalueindex",g,"54533251-82be-4824-96c1-47b60b740d00","0cc5b647-c1df-4637-891a-dec35c318583","0"], capture_output=True)
        subprocess.run(["powercfg","/setdcvalueindex",g,"54533251-82be-4824-96c1-47b60b740d00","0cc5b647-c1df-4637-891a-dec35c318583","0"], capture_output=True)

def t_cpu_priority():
    _reg(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\PriorityControl", "Win32PrioritySeparation", winreg.REG_DWORD, 0x26)

def t_timer_res():
    subprocess.run(["bcdedit","/set","useplatformtick","yes"], capture_output=True)
    subprocess.run(["bcdedit","/set","disabledynamictick","yes"], capture_output=True)

def t_cpu_idle():
    subprocess.run(["powercfg","/setacvalueindex","SCHEME_CURRENT","54533251-82be-4824-96c1-47b60b740d00","5d76a2ca-e8c0-402f-a133-2158492d58ad","0"], capture_output=True)

def t_mm_games():
    base  = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile"
    gbase = base + r"\Tasks\Games"
    _reg(winreg.HKEY_LOCAL_MACHINE, base,  "SystemResponsiveness", winreg.REG_DWORD, 0)
    _reg(winreg.HKEY_LOCAL_MACHINE, gbase, "GPU Priority", winreg.REG_DWORD, 8)
    _reg(winreg.HKEY_LOCAL_MACHINE, gbase, "Priority", winreg.REG_DWORD, 6)
    _reg(winreg.HKEY_LOCAL_MACHINE, gbase, "Scheduling Category", winreg.REG_SZ, "High")

def t_powerthrot():
    _reg(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Power\PowerThrottling", "PowerThrottlingOff", winreg.REG_DWORD, 1)

def t_hpet():
    subprocess.run(["bcdedit","/deletevalue","useplatformclock"], capture_output=True)

# GPU
def t_hw_sched():
    _reg(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers", "HwSchMode", winreg.REG_DWORD, 2)

def t_shader():
    _reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\DirectX\UserGpuPreferences", "DirectXUserGlobalSettings", winreg.REG_SZ, "SwapEffectUpgradeEnable=1;")

def t_mpo():
    _reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\Dwm", "OverlayTestMode", winreg.REG_DWORD, 5)

def t_prerender():
    _reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\DirectX", "MaxRenderedFramesAllowed", winreg.REG_DWORD, 1)

def t_gamemode():
    try:
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\GameBar", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(k, "AllowAutoGameMode", 0, winreg.REG_DWORD, 0)
        winreg.CloseKey(k)
    except: pass

# Network
def t_nagle():
    base = r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces"
    reg  = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base)
    i = 0
    while True:
        try:
            sub = winreg.EnumKey(reg, i)
            k   = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base + "\\" + sub, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(k, "TcpAckFrequency", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(k, "TCPNoDelay", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(k)
            i += 1
        except OSError: break
    winreg.CloseKey(reg)

def t_net_throttle():
    _reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile", "NetworkThrottlingIndex", winreg.REG_DWORD, 0xffffffff)

def t_dns():
    base = r"SYSTEM\CurrentControlSet\Services\Dnscache\Parameters"
    _reg(winreg.HKEY_LOCAL_MACHINE, base, "CacheHashTableBucketSize", winreg.REG_DWORD, 1)
    _reg(winreg.HKEY_LOCAL_MACHINE, base, "CacheHashTableSize", winreg.REG_DWORD, 384)

def t_tcpauto():
    subprocess.run(["netsh","int","tcp","set","global","autotuninglevel=normal"], capture_output=True)

# Services
def t_sysmain():
    subprocess.run(["sc","config","SysMain","start=","disabled"], capture_output=True)
    subprocess.run(["sc","stop","SysMain"], capture_output=True)

def t_search():
    subprocess.run(["sc","config","WSearch","start=","disabled"], capture_output=True)
    subprocess.run(["sc","stop","WSearch"], capture_output=True)

def t_xbox():
    for hive, path, name, rtype, val in [
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\GameDVR", "AppCaptureEnabled", winreg.REG_DWORD, 0),
        (winreg.HKEY_CURRENT_USER, r"System\GameConfigStore", "GameDVR_Enabled", winreg.REG_DWORD, 0),
    ]:
        try:
            k = winreg.OpenKey(hive, path, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(k, name, 0, rtype, val)
            winreg.CloseKey(k)
        except: pass

def t_telemetry():
    for svc in ["DiagTrack","dmwappushservice","WerSvc","PcaSvc"]:
        subprocess.run(["sc","config",svc,"start=","disabled"], capture_output=True)
        subprocess.run(["sc","stop",svc], capture_output=True)
    _reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\DataCollection", "AllowTelemetry", winreg.REG_DWORD, 0)

def t_fse():
    try:
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"System\GameConfigStore", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(k, "GameDVR_DXGIHonorFSEWindowsCompatible", 0, winreg.REG_DWORD, 1)
        winreg.CloseKey(k)
    except: pass

def t_memory():
    base = r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management"
    _reg(winreg.HKEY_LOCAL_MACHINE, base, "DisablePagingExecutive", winreg.REG_DWORD, 1)
    _reg(winreg.HKEY_LOCAL_MACHINE, base, "SystemPages", winreg.REG_DWORD, 0xffffffff)

def t_bgapps():
    try:
        k = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\BackgroundAccessApplications", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(k, "GlobalUserDisabled", 0, winreg.REG_DWORD, 1)
        winreg.CloseKey(k)
    except: pass

def t_visuals():
    try:
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(k, "EnableTransparency", 0, winreg.REG_DWORD, 0)
        winreg.CloseKey(k)
    except: pass

def create_restore_point():
    cmd = 'Checkpoint-Computer -Description "AURA Optimization" -RestorePointType MODIFY_SETTINGS -ErrorAction Stop'
    r = _ps(cmd)
    if r.returncode != 0:
        raise RuntimeError("Enable System Protection on C: via Control Panel > System > System Protection")

TWEAKS = [
    {"id":"perf",    "cat":"CPU",     "impact":"HIGH", "name":"Ultimate Performance Plan", "desc":"Activates hidden max-power plan", "fn":t_high_perf},
    {"id":"parking", "cat":"CPU",     "impact":"HIGH", "name":"Disable Core Parking", "desc":"All cores stay awake", "fn":t_core_parking},
    {"id":"cpuprio", "cat":"CPU",     "impact":"HIGH", "name":"Foreground CPU Priority", "desc":"Max quantum to game thread", "fn":t_cpu_priority},
    {"id":"timer",   "cat":"CPU",     "impact":"HIGH", "name":"1ms Timer Resolution", "desc":"Tightest scheduler tick", "fn":t_timer_res},
    {"id":"idle",    "cat":"CPU",     "impact":"MED",  "name":"Disable CPU Idle States", "desc":"Removes C-state transitions", "fn":t_cpu_idle},
    {"id":"mmgames", "cat":"CPU",     "impact":"HIGH", "name":"Multimedia Game Sched", "desc":"GPU Priority 8 + High Scheduling", "fn":t_mm_games},
    {"id":"pwrthrt", "cat":"CPU",     "impact":"HIGH", "name":"Disable Power Throttling", "desc":"Prevents Windows from throttling processes", "fn":t_powerthrot},
    {"id":"hpet",    "cat":"CPU",     "impact":"HIGH", "name":"Disable HPET", "desc":"Lowers DPC latency", "fn":t_hpet},
    
    {"id":"hwsched", "cat":"GPU",     "impact":"HIGH", "name":"Hardware GPU Scheduler", "desc":"WDDM 2.7 HAGS", "fn":t_hw_sched},
    {"id":"shader",  "cat":"GPU",     "impact":"HIGH", "name":"Unlimited Shader Cache", "desc":"No disk cap on shader store", "fn":t_shader},
    {"id":"mpo",     "cat":"GPU",     "impact":"HIGH", "name":"Disable MPO", "desc":"Fixes stutters on NVIDIA/AMD", "fn":t_mpo},
    {"id":"frames",  "cat":"GPU",     "impact":"HIGH", "name":"Limit Pre-rendered Frames", "desc":"DXGI max 1 frame", "fn":t_prerender},
    {"id":"gamemod", "cat":"GPU",     "impact":"MED",  "name":"Disable Game Mode", "desc":"Prevents background task starvation", "fn":t_gamemode},
    
    {"id":"nagle",   "cat":"Network", "impact":"HIGH", "name":"Disable Nagle Algorithm", "desc":"TCPNoDelay on all interfaces", "fn":t_nagle},
    {"id":"netthrt", "cat":"Network", "impact":"HIGH", "name":"Remove Network Throttle", "desc":"Removes 10 Mbps multimedia cap", "fn":t_net_throttle},
    {"id":"dns",     "cat":"Network", "impact":"MED",  "name":"Maximize DNS Cache", "desc":"Faster server lookups", "fn":t_dns},
    {"id":"tcpauto", "cat":"Network", "impact":"MED",  "name":"TCP Auto-Tuning", "desc":"Optimizes receive window", "fn":t_tcpauto},
    
    {"id":"sysmain", "cat":"Services","impact":"MED",  "name":"Disable SysMain", "desc":"Frees RAM from OS cache", "fn":t_sysmain},
    {"id":"search",  "cat":"Services","impact":"MED",  "name":"Disable Search Indexing", "desc":"Stops background disk I/O", "fn":t_search},
    {"id":"xbox",    "cat":"Services","impact":"MED",  "name":"Disable Xbox Game Bar", "desc":"Removes recording hooks", "fn":t_xbox},
    {"id":"telem",   "cat":"Services","impact":"MED",  "name":"Disable Telemetry", "desc":"Kills DiagTrack, WerSvc", "fn":t_telemetry},
    {"id":"fse",     "cat":"Services","impact":"HIGH", "name":"Fullscreen Exclusive Fix", "desc":"Forces true FSE mode", "fn":t_fse},
    {"id":"memory",  "cat":"Services","impact":"MED",  "name":"Memory Manager Opt", "desc":"DisablePagingExecutive", "fn":t_memory},
    {"id":"bgapps",  "cat":"Services","impact":"MED",  "name":"Disable Background Apps", "desc":"Stops UWP apps running silently", "fn":t_bgapps},
    {"id":"visuals", "cat":"Services","impact":"HIGH", "name":"Optimize Visual Effects", "desc":"Disables transparency", "fn":t_visuals},
]

CATS = ["CPU","GPU","Network","Services"]

# ─────────────────────────────────────────────────────────────────────────────
#  UI (Dark Luxury)
# ─────────────────────────────────────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AURA - Precision Tuning")
        self.geometry("1000x680")
        self.minsize(900, 600)
        self.configure(bg=BG)
        
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

    def _build(self):
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True)
        self._build_sidebar(body)
        tk.Frame(body, bg=BORDER, width=1).pack(side="left", fill="y")
        self._build_main(body)

    def _build_sidebar(self, parent):
        sb = tk.Frame(parent, bg=BG, width=220)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)

        # Logo
        lf = tk.Frame(sb, bg=BG, height=120)
        lf.pack(fill="x")
        lf.pack_propagate(False)
        tk.Label(lf, text="AURA", bg=BG, fg=TEXT, font=("Georgia", 24, "bold"), tracking=5).pack(pady=(30,0))
        tk.Label(lf, text="PRECISION TUNING", bg=BG, fg=ACCENT, font=("Consolas", 8)).pack()

        tk.Frame(sb, bg=BORDER, height=1).pack(fill="x", padx=20, pady=10)

        nav_items = ["Dashboard","CPU","GPU","Network","Services"]
        for label in nav_items:
            outer = tk.Frame(sb, bg=BG, cursor="hand2")
            outer.pack(fill="x", padx=20, pady=4)
            lbl = tk.Label(outer, text=label.upper(), bg=BG, fg=MUTED, font=FONT_MONO, cursor="hand2", anchor="w")
            lbl.pack(side="left", py=12, px=10)
            
            for w in (outer, lbl):
                w.bind("<Button-1>", lambda e, l=label: self._nav(l))
                w.bind("<Enter>",    lambda e, l=label: self._nhover(l, True))
                w.bind("<Leave>",    lambda e, l=label: self._nhover(l, False))
            self._nf[label] = outer
            self._nc[label] = lbl

        # Status
        tk.Frame(sb, bg=BORDER, height=1).pack(fill="x", padx=20, pady=(40,10))
        sf = tk.Frame(sb, bg=BG)
        sf.pack(fill="x", padx=30, pady=10)
        self._dot_cv = tk.Canvas(sf, width=8, height=8, bg=BG, highlightthickness=0)
        self._dot_cv.pack(side="left")
        self._dot_cv.create_oval(0,0,8,8, fill=BORDER, outline="", tags="dot")
        self._stat_lbl = tk.Label(sf, text="STANDBY", bg=BG, fg=MUTED, font=("Consolas", 7))
        self._stat_lbl.pack(side="left", padx=10)

    def _nhover(self, label, on):
        if self.active == label: return
        self._nc[label].config(fg=TEXT if on else MUTED)

    def _nav_activate(self, label):
        self._nc[label].config(fg=ACCENT)
        self._nf[label].config(bg=SURF2)
        self._nc[label].config(bg=SURF2)

    def _nav_deactivate(self, label):
        self._nc[label].config(fg=MUTED)
        self._nf[label].config(bg=BG)
        self._nc[label].config(bg=BG)

    def _nav(self, label):
        if self.active != label:
            self._nav_deactivate(self.active)
        self.active = label
        self._nav_activate(label)
        self._topbar_lbl.config(text=label)
        self._go(label)

    def _build_main(self, parent):
        main = tk.Frame(parent, bg=SURF)
        main.pack(side="left", fill="both", expand=True)

        top = tk.Frame(main, bg=SURF, height=100)
        top.pack(fill="x")
        top.pack_propagate(False)

        tf = tk.Frame(top, bg=SURF)
        tf.pack(side="left", padx=40, pady=30)
        tk.Label(tf, text="CURRENT MODULE", bg=SURF, fg=MUTED, font=("Consolas", 7), anchor="w").pack(fill="x")
        self._topbar_lbl = tk.Label(tf, text="Dashboard", bg=SURF, fg=TEXT, font=FONT_SERIF, anchor="w")
        self._topbar_lbl.pack(fill="x")

        self._apply_btn = tk.Button(
            top, text="DEPLOY CONFIGURATION", bg=SURF2, fg=ACCENT, font=FONT_MONO,
            relief="flat", cursor="hand2", padx=20, pady=8, bd=1, highlightbackground=ACCENT,
            command=self._start_apply, activebackground=ACCENT, activeforeground=BG)
        self._apply_btn.pack(side="right", padx=40, pady=30)

        wrap = tk.Frame(main, bg=SURF)
        wrap.pack(fill="both", expand=True, padx=40, pady=(0,40))

        self._canvas = tk.Canvas(wrap, bg=SURF, highlightthickness=0, bd=0)
        vsb = tk.Scrollbar(wrap, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._inner = tk.Frame(self._canvas, bg=SURF)
        self._cwin  = self._canvas.create_window((0,0), window=self._inner, anchor="nw")
        self._inner.bind("<Configure>", lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>", lambda e: self._canvas.itemconfig(self._cwin, width=e.width))
        self._canvas.bind("<MouseWheel>", lambda e: self._canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

    def _clear(self):
        for w in self._inner.winfo_children(): w.destroy()
        self._log_w = None
        self._canvas.yview_moveto(0)

    def _go(self, name):
        self._clear()
        if name == "Dashboard": self._page_dash()
        else: self._page_tweaks(name)

    def _sec_label(self, parent, title, sub):
        row = tk.Frame(parent, bg=SURF)
        row.pack(fill="x", pady=(20, 10))
        tk.Label(row, text=title, bg=SURF, fg=TEXT, font=FONT_SERIF_L).pack(anchor="w")
        tk.Label(row, text=sub.upper(), bg=SURF, fg=ACCENT, font=("Consolas", 7)).pack(anchor="w", pady=(4,0))
        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", pady=(10,20))

    def _page_dash(self):
        p = self._inner
        
        # Hero
        hf = tk.Frame(p, bg=SURF)
        hf.pack(fill="x", pady=(10, 30))
        tk.Label(hf, text="Uncompromised", bg=SURF, fg=TEXT, font=("Georgia", 36)).pack(anchor="w")
        tk.Label(hf, text="Performance.", bg=SURF, fg=ACCENT, font=("Georgia", 36, "italic")).pack(anchor="w")
        tk.Label(hf, text="Elite system optimization utility. Select your parameters and deploy.", bg=SURF, fg=MUTED, font=FONT_SANS).pack(anchor="w", pady=(10,0))

        self._sec_label(p, "Telemetry", "System Overview")

        stat_row = tk.Frame(p, bg=BORDER)
        stat_row.pack(fill="x", pady=(0,20))
        
        for label, val, color in [
            ("Total Modules", str(len(TWEAKS)), TEXT),
            ("Active Modules", str(sum(1 for t in TWEAKS if self.vars[t["id"]].get())), ACCENT),
            ("Integrity Check", "Secured" if self.restore_done else "Pending", TEXT if self.restore_done else MUTED),
        ]:
            card = tk.Frame(stat_row, bg=SURF)
            card.pack(side="left", expand=True, fill="both", padx=1, pady=1)
            tk.Label(card, text=label.upper(), bg=SURF, fg=MUTED, font=("Consolas", 7)).pack(pady=(20,10))
            tk.Label(card, text=val, bg=SURF, fg=color, font=("Georgia", 24)).pack(pady=(0,20))

        self._sec_label(p, "Console", "Execution Log")
        host = tk.Frame(p, bg=BG, highlightbackground=BORDER, highlightthickness=1)
        host.pack(fill="both", expand=True, pady=(0,20))

        self._log_w = tk.Text(host, bg=BG, fg=MUTED, font=FONT_MONO, relief="flat", bd=0, height=12, state="disabled", padx=20, pady=20)
        self._log_w.pack(fill="both", expand=True)
        self._log_w.tag_configure("ts", foreground=BORDER)
        self._log_w.tag_configure("ok", foreground=TEXT)
        self._log_w.tag_configure("info", foreground=ACCENT)
        self._log_w.tag_configure("warn", foreground="#a38a2c")
        self._log_w.tag_configure("err", foreground="#ff4444")

        self._log(f"System analysis complete. {len(TWEAKS)} optimizations available.", "ok")
        self._log("Awaiting execution command.", "info")

    def _page_tweaks(self, cat):
        p = self._inner
        lst = [t for t in TWEAKS if t["cat"]==cat]
        self._sec_label(p, cat, "Configuration Parameters")
        
        for t in lst:
            self._tweak_card(p, t, self.vars[t["id"]])

    def _tweak_card(self, parent, tweak, var):
        outer = tk.Frame(parent, bg=SURF)
        outer.pack(fill="x", pady=0)
        
        content = tk.Frame(outer, bg=SURF)
        content.pack(fill="x", pady=16)
        
        left = tk.Frame(content, bg=SURF)
        left.pack(side="left", fill="x", expand=True)
        
        tr = tk.Frame(left, bg=SURF)
        tr.pack(fill="x", anchor="w")
        tk.Label(tr, text=tweak["name"], bg=SURF, fg=TEXT, font=("Georgia", 12)).pack(side="left")
        if tweak["impact"] == "HIGH":
            tk.Label(tr, text="HIGH IMPACT", bg=SURF, fg=ACCENT, font=("Consolas", 7), bd=1, relief="solid").pack(side="left", padx=10)
            
        tk.Label(left, text=tweak["desc"], bg=SURF, fg=MUTED, font=FONT_SANS).pack(fill="x", anchor="w", pady=(4,0))

        self._toggle(content, var)
        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x")

    def _toggle(self, parent, var):
        W, H, R = 40, 20, 10
        cv = tk.Canvas(parent, width=W, height=H, bg=SURF, highlightthickness=0, cursor="hand2")
        cv.pack(side="right", padx=10)

        def draw(*_):
            cv.delete("all")
            on = var.get()
            col = ACCENT if on else BORDER
            cv.create_oval(0, 0, H, H, fill=col if on else SURF, outline=col)
            cv.create_oval(W-H, 0, W, H, fill=col if on else SURF, outline=col)
            cv.create_rectangle(R, 0, W-R, H, fill=col if on else SURF, outline=col)
            kx = W-H+2 if on else 2
            cv.create_oval(kx, 2, kx+H-4, H-2, fill=BG if on else MUTED, outline="")

        draw()
        var.trace_add("write", draw)
        cv.bind("<Button-1>", lambda e: var.set(not var.get()))

    def _start_apply(self):
        if self.applying: return
        sel = [t for t in TWEAKS if self.vars[t["id"]].get()]
        if not sel:
            messagebox.showwarning("AURA", "Select at least one optimization parameter.")
            return
        if not messagebox.askyesno("AURA", f"Initiating deployment of {len(sel)} optimizations.\n\nA System Restore Point will be created to ensure system integrity.\nProceed with deployment?"):
            return
        self._nav("Dashboard")
        self.after(100, lambda: self._run(sel))

    def _run(self, sel):
        self.applying = True
        self._apply_btn.config(state="disabled", text="DEPLOYING...", bg=BG)
        self._dot_cv.itemconfig("dot", fill=ACCENT)
        self._stat_lbl.config(text="EXECUTING...")
        threading.Thread(target=self._worker, args=(sel,), daemon=True).start()

    def _worker(self, sel):
        try:
            self._log("Establishing System Restore Point...", "warn")
            create_restore_point()
            self.restore_done = True
            self._log("Restore Point established successfully.", "ok")

            ok = fail = 0
            for t in sel:
                self._log(f"Executing: {t['name']}...", "info")
                try:
                    t["fn"]()
                    self._log(f"  {t['name']} applied.", "ok")
                    ok += 1
                except Exception as e:
                    self._log(f"  {t['name']} FAILED: {e}", "err")
                    fail += 1
                time.sleep(0.1)

            self._log("---", "ts")
            self._log(f"Deployment finalized: {ok} successful, {fail} failed.", "ok")
            self._log("System reboot required to commit changes.", "warn")
            self.after(0, self._done, ok, fail)

        except Exception as e:
            self._log(f"FATAL: {e}", "err")
            self.after(0, self._err_cb, str(e))

    def _log(self, msg, tag="info"):
        def _do():
            if not self._log_w or not self._log_w.winfo_exists(): return
            self._log_w.config(state="normal")
            ts = datetime.datetime.now().strftime("%H:%M:%S")
            self._log_w.insert("end", f"\n[{ts}]  ", "ts")
            self._log_w.insert("end", msg, tag)
            self._log_w.config(state="disabled")
            self._log_w.see("end")
        if threading.current_thread() is threading.main_thread(): _do()
        else: self.after(0, _do)

    def _done(self, ok, fail):
        self.applying = False
        self._apply_btn.config(state="normal", text="DEPLOY CONFIGURATION", bg=SURF2)
        self._dot_cv.itemconfig("dot", fill=BORDER)
        self._stat_lbl.config(text="STANDBY")
        messagebox.showinfo("AURA", f"Deployment finalized.\n{ok} applied, {fail} failed.\n\nSystem reboot required.")

    def _err_cb(self, err):
        self.applying = False
        self._apply_btn.config(state="normal", text="DEPLOY CONFIGURATION", bg=SURF2)
        self._dot_cv.itemconfig("dot", fill="#ff4444")
        self._stat_lbl.config(text="ERROR")
        messagebox.showerror("AURA Error", f"Failed to create restore point:\n\n{err}\n\nEnable System Protection on C: drive.")

if __name__ == "__main__":
    app = App()
    app.mainloop()
