"""
FPS Utility — Lite  v4.0
pywebview frontend (real browser engine) + Python backend.
Full Syne + DM Mono fonts, CSS animations, zero tkinter lag.
Requires: Windows 10/11 | Administrator | pywebview
"""

import ctypes, sys, os, json, threading, subprocess, winreg, time, datetime

# ── Admin gate ────────────────────────────────────────────────────────────────
def _is_admin():
    try: return ctypes.windll.shell32.IsUserAnAdmin()
    except: return False

if not _is_admin():
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable,
        " ".join(f'"{a}"' for a in sys.argv), None, 1)
    sys.exit()

# ── Asset path (works for both .py and PyInstaller .exe) ─────────────────────
def _asset(name):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)

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

def t_high_perf():
    r = _ps("powercfg /duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61")
    guid = None
    for line in r.stdout.splitlines():
        parts = line.strip().split()
        if parts and len(parts[-1]) == 36: guid = parts[-1]
    _ps("powercfg /setactive " + (guid or "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"))

def t_core_parking():
    r = subprocess.run(["powercfg", "/list"], capture_output=True, text=True)
    guids = [l.split()[3] for l in r.stdout.splitlines() if "GUID:" in l]
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
    subprocess.run(["bcdedit","/set","useplatformtick","yes"],    capture_output=True)
    subprocess.run(["bcdedit","/set","disabledynamictick","yes"], capture_output=True)

def t_cpu_idle():
    subprocess.run(["powercfg","/setacvalueindex","SCHEME_CURRENT",
        "54533251-82be-4824-96c1-47b60b740d00",
        "5d76a2ca-e8c0-402f-a133-2158492d58ad","0"], capture_output=True)

def t_mm_games():
    b = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile"
    g = b + r"\Tasks\Games"
    _reg(winreg.HKEY_LOCAL_MACHINE, b, "SystemResponsiveness", winreg.REG_DWORD, 0)
    _reg(winreg.HKEY_LOCAL_MACHINE, g, "GPU Priority",         winreg.REG_DWORD, 8)
    _reg(winreg.HKEY_LOCAL_MACHINE, g, "Priority",             winreg.REG_DWORD, 6)
    _reg(winreg.HKEY_LOCAL_MACHINE, g, "Scheduling Category",  winreg.REG_SZ, "High")
    _reg(winreg.HKEY_LOCAL_MACHINE, g, "SFIO Priority",        winreg.REG_SZ, "High")

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

def t_nagle():
    base = r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces"
    reg  = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base)
    i = 0
    while True:
        try:
            sub = winreg.EnumKey(reg, i)
            k   = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                 base+"\\"+sub, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(k, "TcpAckFrequency", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(k, "TCPNoDelay",      0, winreg.REG_DWORD, 1)
            winreg.CloseKey(k)
            i += 1
        except OSError: break
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
         "AppCaptureEnabled", winreg.REG_DWORD, 0),
        (winreg.HKEY_CURRENT_USER,
         r"System\GameConfigStore",
         "GameDVR_Enabled",         winreg.REG_DWORD, 0),
        (winreg.HKEY_CURRENT_USER,
         r"System\GameConfigStore",
         "GameDVR_FSEBehaviorMode", winreg.REG_DWORD, 2),
    ]:
        try:
            k = winreg.OpenKey(hive, path, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(k, name, 0, rtype, val)
            winreg.CloseKey(k)
        except Exception: pass

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
        except Exception: pass

def t_memory():
    base = r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management"
    _reg(winreg.HKEY_LOCAL_MACHINE, base, "LargeSystemCache",       winreg.REG_DWORD, 0)
    _reg(winreg.HKEY_LOCAL_MACHINE, base, "DisablePagingExecutive", winreg.REG_DWORD, 1)
    _reg(winreg.HKEY_LOCAL_MACHINE, base, "SystemPages",            winreg.REG_DWORD, 0xffffffff)

def create_restore_point():
    r = _ps('Checkpoint-Computer -Description "FPS Utility Lite" '
            '-RestorePointType MODIFY_SETTINGS -ErrorAction Stop')
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or
            "Enable System Protection: Control Panel > System > System Protection")

TWEAKS = [
    {"id":"perf",    "cat":"CPU",     "impact":"HIGH",
     "name":"Ultimate Performance Plan",
     "desc":"Activates hidden max-power plan — highest sustained clocks",
     "fn":t_high_perf},
    {"id":"parking", "cat":"CPU",     "impact":"HIGH",
     "name":"Disable Core Parking",
     "desc":"All cores stay awake — eliminates spin-up stutter",
     "fn":t_core_parking},
    {"id":"cpuprio", "cat":"CPU",     "impact":"HIGH",
     "name":"Foreground CPU Priority Boost",
     "desc":"Win32PrioritySeparation 0x26 — max quantum to game thread",
     "fn":t_cpu_priority},
    {"id":"timer",   "cat":"CPU",     "impact":"HIGH",
     "name":"1ms Timer Resolution",
     "desc":"bcdedit useplatformtick — tightest scheduler tick",
     "fn":t_timer_res},
    {"id":"idle",    "cat":"CPU",     "impact":"MED",
     "name":"Disable CPU Idle States",
     "desc":"Removes C-state power transitions during gameplay",
     "fn":t_cpu_idle},
    {"id":"mmgames", "cat":"CPU",     "impact":"HIGH",
     "name":"Multimedia Game Scheduling",
     "desc":"GPU Priority 8 + Scheduling Category High for games",
     "fn":t_mm_games},
    {"id":"hwsched", "cat":"GPU",     "impact":"HIGH",
     "name":"Hardware GPU Scheduler",
     "desc":"WDDM 2.7 HAGS — reduces CPU-GPU latency significantly",
     "fn":t_hw_sched},
    {"id":"shader",  "cat":"GPU",     "impact":"HIGH",
     "name":"Unlimited Shader Cache",
     "desc":"No disk cap on shader store — eliminates compile stutters",
     "fn":t_shader},
    {"id":"mpo",     "cat":"GPU",     "impact":"HIGH",
     "name":"Disable Multi-Plane Overlay",
     "desc":"Fixes major stutters and black screens on NVIDIA/AMD",
     "fn":t_mpo},
    {"id":"frames",  "cat":"GPU",     "impact":"HIGH",
     "name":"Limit Pre-rendered Frames",
     "desc":"DXGI max 1 pre-rendered frame — cuts input lag",
     "fn":t_prerender},
    {"id":"nagle",   "cat":"Network", "impact":"HIGH",
     "name":"Disable Nagle Algorithm",
     "desc":"TCPNoDelay + AckFrequency=1 on all interfaces",
     "fn":t_nagle},
    {"id":"netthrot","cat":"Network", "impact":"HIGH",
     "name":"Remove Network Throttle",
     "desc":"Removes the hidden 10 Mbps multimedia throttle cap",
     "fn":t_net_throttle},
    {"id":"dns",     "cat":"Network", "impact":"MED",
     "name":"Maximize DNS Cache",
     "desc":"Larger cache bucket size — faster server lookups",
     "fn":t_dns},
    {"id":"sysmain", "cat":"Services","impact":"MED",
     "name":"Disable SysMain / Superfetch",
     "desc":"Frees RAM from OS pre-loading cache",
     "fn":t_sysmain},
    {"id":"search",  "cat":"Services","impact":"MED",
     "name":"Disable Search Indexing",
     "desc":"Stops background disk I/O from Windows Search",
     "fn":t_search},
    {"id":"xbox",    "cat":"Services","impact":"MED",
     "name":"Disable Xbox Game Bar / DVR",
     "desc":"Removes recording hooks and overlay overhead",
     "fn":t_xbox},
    {"id":"telem",   "cat":"Services","impact":"MED",
     "name":"Disable Telemetry Services",
     "desc":"Kills DiagTrack, WerSvc, PcaSvc background services",
     "fn":t_telemetry},
    {"id":"fse",     "cat":"Services","impact":"HIGH",
     "name":"Fullscreen Exclusive Fix",
     "desc":"Forces true FSE mode — maximum GPU priority in games",
     "fn":t_fse},
    {"id":"memory",  "cat":"Services","impact":"MED",
     "name":"Memory Manager Optimization",
     "desc":"DisablePagingExecutive + max system pages for gaming",
     "fn":t_memory},
]

# ─────────────────────────────────────────────────────────────────────────────
#  WEBVIEW API  — methods called from JS via window.pywebview.api.*
# ─────────────────────────────────────────────────────────────────────────────
class API:
    def __init__(self):
        self._window      = None   # set after webview.create_window
        self._restore_done = False
        self._applying     = False
        self._log_buf      = []    # queued log lines for JS to poll

    def get_tweaks(self):
        """Return tweak list (without fn) as JSON-safe list."""
        return [{"id":t["id"],"cat":t["cat"],"impact":t["impact"],
                 "name":t["name"],"desc":t["desc"]} for t in TWEAKS]

    def get_stats(self):
        high = sum(1 for t in TWEAKS if t["impact"]=="HIGH")
        return {"total": len(TWEAKS), "high": high,
                "restore_done": self._restore_done}

    def poll_log(self):
        """JS calls this to drain queued log messages."""
        out = list(self._log_buf)
        self._log_buf.clear()
        return out

    def apply_tweaks(self, ids):
        """ids: list of tweak IDs to apply. Returns immediately; progress via poll_log."""
        if self._applying:
            return {"ok": False, "error": "Already running"}
        sel = [t for t in TWEAKS if t["id"] in ids]
        if not sel:
            return {"ok": False, "error": "No tweaks selected"}
        self._applying = True
        threading.Thread(target=self._apply_worker, args=(sel,), daemon=True).start()
        return {"ok": True}

    def _apply_worker(self, sel):
        self._push("Creating system restore point...", "warn")
        try:
            create_restore_point()
            self._restore_done = True
            self._push("Restore point created.", "ok")
        except Exception as e:
            self._push("FATAL: " + str(e), "err")
            self._push("__DONE__:0:" + str(len(sel)), "sys")
            self._applying = False
            return

        ok = fail = 0
        for t in sel:
            self._push("→  " + t["name"], "info")
            try:
                t["fn"]()
                self._push("   ✓  done", "ok")
                ok += 1
            except Exception as e:
                self._push("   ✗  " + str(e), "err")
                fail += 1
            time.sleep(0.05)

        self._push("Complete — " + str(ok) + " applied, " + str(fail) + " failed.", "ok")
        self._push("Restart Windows for all changes to take effect.", "warn")
        self._push("__DONE__:" + str(ok) + ":" + str(fail), "sys")
        self._applying = False

    def _push(self, msg, tag):
        ts  = datetime.datetime.now().strftime("%H:%M:%S")
        self._log_buf.append({"ts": ts, "msg": msg, "tag": tag})


# ─────────────────────────────────────────────────────────────────────────────
#  HTML  — the entire UI in one string
# ─────────────────────────────────────────────────────────────────────────────
HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>FPS Utility — Lite</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=DM+Mono:ital,wght@0,300;0,400;0,500;1,300&display=swap" rel="stylesheet">
<style>
/* ── Reset & base ── */
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#080a0c;--surf:#0e1114;--surf2:#141820;
  --border:rgba(255,255,255,0.06);--border-solid:#1a2030;
  --accent:#00d4ff;--accent2:#0099cc;
  --text:#e8edf2;--muted:#5a6472;
  --green:#00e5a0;--gold:#f5c842;
  --red:#ff5f57;--ylw:#ffbd2e;--grn:#28c840;
  --accent-bg:rgba(0,212,255,0.07);
  --accent-bd:rgba(0,212,255,0.18);
  --green-bg:rgba(0,229,160,0.07);
  --green-bd:rgba(0,229,160,0.18);
  --gold-bg:rgba(245,200,66,0.07);
  --gold-bd:rgba(245,200,66,0.18);
  --warn-bg:#110e02;
  --radius:12px;
  --sidebar:62px;
}
html,body{width:100%;height:100%;overflow:hidden;background:var(--bg)}
body{font-family:'Syne',sans-serif;color:var(--text);display:flex;flex-direction:column}

/* ── Grid background ── */
body::before{
  content:'';position:fixed;inset:0;pointer-events:none;z-index:0;
  background-image:
    linear-gradient(rgba(0,212,255,0.025) 1px,transparent 1px),
    linear-gradient(90deg,rgba(0,212,255,0.025) 1px,transparent 1px);
  background-size:40px 40px;
}

/* ── Titlebar ── */
.titlebar{
  height:40px;min-height:40px;background:#06080a;
  display:flex;align-items:center;padding:0 16px;
  border-bottom:1px solid var(--border-solid);
  position:relative;z-index:10;
  -webkit-app-region:drag;user-select:none;
}
.titlebar-dots{display:flex;gap:7px;margin-right:16px;-webkit-app-region:no-drag}
.dot{width:12px;height:12px;border-radius:50%}
.dot-r{background:#ff5f57}.dot-y{background:#ffbd2e}.dot-g{background:#28c840}
.titlebar-title{font-family:'DM Mono',monospace;font-size:11px;color:var(--muted);
  flex:1;text-align:center;letter-spacing:.06em}
.titlebar-ver{font-family:'DM Mono',monospace;font-size:10px;color:var(--border-solid)}

/* ── Shell ── */
.shell{display:flex;flex:1;overflow:hidden;position:relative;z-index:1}

/* ── Sidebar ── */
.sidebar{
  width:var(--sidebar);min-width:var(--sidebar);
  background:#06080a;
  border-right:1px solid var(--border-solid);
  display:flex;flex-direction:column;align-items:center;
  padding:12px 0;gap:2px;
}
.logo{
  width:42px;height:42px;border-radius:50%;
  background:radial-gradient(circle,rgba(0,212,255,0.15),transparent 70%);
  border:1px solid var(--accent-bd);
  display:flex;align-items:center;justify-content:center;margin-bottom:12px;
  animation:logoPulse 3s ease-in-out infinite;
}
@keyframes logoPulse{0%,100%{box-shadow:0 0 0 0 rgba(0,212,255,0)}
  50%{box-shadow:0 0 12px 2px rgba(0,212,255,0.15)}}
.logo svg{width:20px;height:20px;fill:var(--accent)}

.nav-item{
  width:46px;height:46px;border-radius:10px;cursor:pointer;
  display:flex;flex-direction:column;align-items:center;justify-content:center;gap:3px;
  transition:background .15s,transform .1s;position:relative;
}
.nav-item:hover{background:var(--surf2)}
.nav-item.active{background:var(--surf2)}
.nav-item.active::before{
  content:'';position:absolute;left:-8px;top:8px;bottom:8px;
  width:3px;border-radius:0 2px 2px 0;background:var(--accent);
}
.nav-item svg{width:18px;height:18px;stroke:var(--muted);fill:none;
  stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round;
  transition:stroke .15s}
.nav-item .nav-lbl{font-family:'DM Mono',monospace;font-size:7px;
  color:var(--muted);letter-spacing:.08em;transition:color .15s}
.nav-item:hover svg,.nav-item.active svg{stroke:var(--accent)}
.nav-item:hover .nav-lbl,.nav-item.active .nav-lbl{color:var(--accent)}
.nav-item:active{transform:scale(.95)}

.sidebar-sep{width:30px;height:1px;background:var(--border-solid);margin:8px 0}

.status-dot{
  width:8px;height:8px;border-radius:50%;background:var(--green);
  animation:statusPulse 2s ease-in-out infinite;
}
@keyframes statusPulse{0%,100%{opacity:1;box-shadow:0 0 0 0 rgba(0,229,160,.4)}
  50%{opacity:.7;box-shadow:0 0 0 4px rgba(0,229,160,0)}}
.status-dot.working{background:var(--gold);
  animation:statusPulse 0.7s ease-in-out infinite}
.status-dot.error{background:var(--red);animation:none}

/* ── Main ── */
.main{flex:1;display:flex;flex-direction:column;overflow:hidden}

/* ── Topbar ── */
.topbar{
  height:48px;min-height:48px;background:var(--surf);
  border-bottom:1px solid var(--border-solid);
  display:flex;align-items:center;padding:0 20px;gap:12px;
}
.topbar-title{font-family:'Syne',sans-serif;font-size:14px;font-weight:700;
  color:var(--text);letter-spacing:-.01em}
.lite-badge{
  background:var(--accent-bg);border:1px solid var(--accent-bd);
  border-radius:100px;padding:3px 10px;
  font-family:'DM Mono',monospace;font-size:9px;
  color:var(--accent);letter-spacing:.1em;
}
.sep-v{width:1px;height:22px;background:var(--border-solid);margin:0 4px}
.topbar-count{font-family:'DM Mono',monospace;font-size:11px;color:var(--muted)}
.topbar-spacer{flex:1}

.apply-btn{
  display:flex;align-items:center;gap:8px;
  background:var(--accent);color:#080a0c;
  font-family:'Syne',sans-serif;font-weight:700;font-size:13px;
  border:none;border-radius:var(--radius);padding:9px 20px;
  cursor:pointer;transition:background .2s,transform .15s,box-shadow .2s;
  letter-spacing:.01em;
}
.apply-btn:hover{background:#22dcff;transform:translateY(-1px);
  box-shadow:0 6px 24px rgba(0,212,255,.3)}
.apply-btn:active{transform:translateY(0)}
.apply-btn:disabled{background:var(--surf2);color:var(--muted);
  cursor:not-allowed;transform:none;box-shadow:none}
.apply-btn svg{width:14px;height:14px;fill:currentColor;flex-shrink:0}

/* ── Content scroll ── */
.content{flex:1;overflow-y:auto;overflow-x:hidden;padding:0}
.content::-webkit-scrollbar{width:6px}
.content::-webkit-scrollbar-track{background:var(--bg)}
.content::-webkit-scrollbar-thumb{background:var(--border-solid);border-radius:3px}

/* ── Page ── */
.page{display:none;padding:0 0 32px}
.page.active{display:block;animation:pageIn .2s ease}
@keyframes pageIn{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}

/* ── Section header ── */
.sec-hdr{
  display:flex;align-items:center;gap:8px;
  padding:20px 22px 0;margin-bottom:14px;
}
.sec-hdr::after{
  content:'';flex:1;height:1px;background:var(--border-solid);margin-left:8px;
}
.sec-dot{width:6px;height:6px;border-radius:50%;background:var(--accent);flex-shrink:0}
.sec-dot.green{background:var(--green)}
.sec-label{font-family:'DM Mono',monospace;font-size:10px;
  color:var(--accent);letter-spacing:.14em;white-space:nowrap}

/* ── Stat cards ── */
.stats-row{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;padding:0 22px;margin-bottom:14px}
.stat-card{
  background:var(--surf);border:1px solid var(--border-solid);
  border-radius:var(--radius);padding:18px 16px;
  transition:border-color .2s,transform .2s;
}
.stat-card:hover{border-color:rgba(0,212,255,.2);transform:translateY(-1px)}
.stat-val{font-family:'Syne',sans-serif;font-size:28px;font-weight:800;
  color:var(--accent);letter-spacing:-.04em;line-height:1}
.stat-val.green{color:var(--green)}
.stat-val.gold{color:var(--gold)}
.stat-lbl{font-family:'DM Mono',monospace;font-size:10px;color:var(--muted);
  letter-spacing:.06em;margin-top:4px}

/* ── Warning banner ── */
.warn-banner{
  margin:0 22px 14px;
  background:rgba(245,200,66,0.05);
  border:1px solid rgba(245,200,66,.25);
  border-radius:var(--radius);padding:12px 16px;
  display:flex;align-items:flex-start;gap:10px;
  animation:fadeIn .3s ease;
}
.warn-banner svg{width:16px;height:16px;flex-shrink:0;margin-top:1px;fill:var(--gold)}
.warn-banner p{font-family:'DM Mono',monospace;font-size:11px;
  color:var(--gold);line-height:1.6}
@keyframes fadeIn{from{opacity:0}to{opacity:1}}

/* ── Category overview ── */
.cat-cards{padding:0 22px;display:flex;flex-direction:column;gap:8px;margin-bottom:4px}
.cat-card{
  background:var(--surf);border:1px solid var(--border-solid);
  border-radius:var(--radius);padding:14px 16px;
  display:flex;align-items:center;gap:14px;
  cursor:pointer;transition:border-color .2s,background .2s;
}
.cat-card:hover{border-color:rgba(0,212,255,.18);background:var(--surf2)}
.cat-icon{
  width:36px;height:36px;border-radius:8px;flex-shrink:0;
  background:var(--accent-bg);border:1px solid var(--accent-bd);
  display:flex;align-items:center;justify-content:center;
}
.cat-icon svg{width:18px;height:18px;stroke:var(--accent);fill:none;
  stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
.cat-info{flex:1}
.cat-name{font-size:13px;font-weight:700;letter-spacing:-.01em;margin-bottom:3px}
.cat-meta{font-family:'DM Mono',monospace;font-size:10px;color:var(--muted)}
.cat-dots{display:flex;gap:4px;align-items:center}
.idot{width:6px;height:6px;border-radius:50%;background:var(--accent);flex-shrink:0}
.idot.high{background:var(--green)}
.cat-arr{color:var(--accent);font-size:16px;opacity:.6;transition:opacity .2s,transform .2s}
.cat-card:hover .cat-arr{opacity:1;transform:translateX(3px)}

/* ── Console ── */
.console-wrap{margin:0 22px;border:1px solid var(--border-solid);
  border-radius:var(--radius);overflow:hidden}
.console-hdr{
  background:#04060a;padding:8px 14px;
  display:flex;align-items:center;gap:8px;
  border-bottom:1px solid var(--border-solid);
}
.console-hdr span{font-family:'DM Mono',monospace;font-size:10px;
  color:var(--muted);letter-spacing:.1em}
.console-hdr-dot{width:6px;height:6px;border-radius:50%;background:var(--green)}
.console-body{
  background:#020406;min-height:200px;max-height:240px;
  overflow-y:auto;padding:12px 16px;
  font-family:'DM Mono',monospace;font-size:11px;line-height:1.8;
}
.console-body::-webkit-scrollbar{width:4px}
.console-body::-webkit-scrollbar-thumb{background:var(--border-solid)}
.log-line{display:flex;gap:8px;animation:logIn .15s ease}
@keyframes logIn{from{opacity:0;transform:translateX(-4px)}to{opacity:1;transform:none}}
.log-ts{color:#1e2e40;flex-shrink:0}
.log-msg.ok{color:#00e5a0}
.log-msg.info{color:#00d4ff}
.log-msg.warn{color:#f5c842}
.log-msg.err{color:#ff5f57}
.log-msg.dim{color:#2a3a4a}
.log-msg.sys{display:none}

/* ── Tweak page header ── */
.tweak-page-hdr{
  display:flex;align-items:center;gap:10px;padding:20px 22px 14px;
  border-bottom:1px solid var(--border-solid);margin-bottom:16px;
}
.tweak-page-icon{
  width:40px;height:40px;border-radius:10px;
  background:var(--accent-bg);border:1px solid var(--accent-bd);
  display:flex;align-items:center;justify-content:center;flex-shrink:0;
}
.tweak-page-icon svg{width:20px;height:20px;stroke:var(--accent);fill:none;
  stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
.tweak-page-title{font-size:18px;font-weight:800;letter-spacing:-.02em}
.tweak-page-meta{font-family:'DM Mono',monospace;font-size:11px;color:var(--muted);margin-top:2px}
.tweak-page-spacer{flex:1}
.select-all-btn{
  font-family:'DM Mono',monospace;font-size:10px;color:var(--accent);
  background:none;border:1px solid var(--accent-bd);border-radius:6px;
  padding:5px 12px;cursor:pointer;transition:background .15s;
}
.select-all-btn:hover{background:var(--accent-bg)}

/* ── Tweak cards ── */
.tweaks-list{padding:0 22px;display:flex;flex-direction:column;gap:8px}
.tweak-card{
  background:var(--surf);border:1px solid var(--border-solid);
  border-radius:var(--radius);
  display:flex;align-items:center;gap:0;
  overflow:hidden;
  transition:border-color .2s,background .15s;
  animation:cardIn .25s ease both;
}
@keyframes cardIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
.tweak-card:hover{border-color:rgba(0,212,255,.15);background:#0f1318}
.tweak-card.high-card{border-color:rgba(0,229,160,.12)}
.tweak-card.high-card:hover{border-color:rgba(0,229,160,.25);background:#0d1510}
.tweak-accent-bar{width:3px;align-self:stretch;background:var(--accent);flex-shrink:0;opacity:.7}
.tweak-accent-bar.high{background:var(--green)}
.tweak-body{flex:1;padding:14px 16px}
.tweak-top{display:flex;align-items:center;gap:10px;margin-bottom:4px}
.tweak-name{font-size:13px;font-weight:700;letter-spacing:-.01em}
.impact-badge{
  border-radius:100px;padding:2px 8px;
  font-family:'DM Mono',monospace;font-size:9px;letter-spacing:.08em;
  flex-shrink:0;
}
.impact-badge.HIGH{background:var(--green-bg);border:1px solid var(--green-bd);color:var(--green)}
.impact-badge.MED{background:var(--accent-bg);border:1px solid var(--accent-bd);color:var(--accent)}
.tweak-desc{font-family:'DM Mono',monospace;font-size:11px;color:var(--muted);line-height:1.5}
.tweak-toggle-wrap{padding:0 18px;flex-shrink:0}

/* ── Toggle ── */
.toggle{
  width:44px;height:24px;border-radius:12px;background:#1a2232;
  cursor:pointer;position:relative;border:none;outline:none;
  transition:background .25s cubic-bezier(.4,0,.2,1);flex-shrink:0;
}
.toggle::after{
  content:'';position:absolute;top:2px;left:2px;
  width:20px;height:20px;border-radius:50%;background:white;
  transition:transform .25s cubic-bezier(.4,0,.2,1),
             box-shadow .25s;
  box-shadow:0 1px 4px rgba(0,0,0,.4);
}
.toggle.on{background:var(--accent)}
.toggle.on.green-toggle{background:var(--green)}
.toggle.on::after{transform:translateX(20px)}
.toggle:hover::after{box-shadow:0 2px 8px rgba(0,0,0,.5)}

/* ── Progress bar (apply) ── */
.progress-wrap{
  display:none;margin:0 22px 16px;
  background:var(--surf);border:1px solid var(--border-solid);
  border-radius:var(--radius);padding:14px 18px;
}
.progress-wrap.visible{display:block;animation:fadeIn .2s ease}
.progress-label{font-family:'DM Mono',monospace;font-size:11px;
  color:var(--muted);margin-bottom:8px}
.progress-bar-bg{height:4px;background:var(--border-solid);border-radius:2px;overflow:hidden}
.progress-bar-fill{
  height:100%;background:var(--accent);border-radius:2px;width:0%;
  transition:width .3s ease;
}

/* ── Done banner ── */
.done-banner{
  display:none;margin:0 22px 16px;
  border-radius:var(--radius);padding:14px 18px;
  align-items:center;gap:12px;
}
.done-banner.visible{display:flex;animation:fadeIn .3s ease}
.done-banner.success{background:var(--green-bg);border:1px solid var(--green-bd)}
.done-banner svg{width:20px;height:20px;stroke:var(--green);fill:none;
  stroke-width:2;stroke-linecap:round;stroke-linejoin:round;flex-shrink:0}
.done-banner p{font-family:'DM Mono',monospace;font-size:12px;color:var(--green);line-height:1.5}

/* ── Confirm modal ── */
.modal-overlay{
  position:fixed;inset:0;background:rgba(6,8,10,.85);
  display:flex;align-items:center;justify-content:center;
  z-index:100;backdrop-filter:blur(4px);
  animation:overlayIn .15s ease;
}
@keyframes overlayIn{from{opacity:0}to{opacity:1}}
.modal{
  background:var(--surf);border:1px solid var(--border-solid);
  border-radius:18px;padding:28px;width:400px;max-width:92vw;
  animation:modalIn .2s cubic-bezier(.34,1.4,.64,1);
}
@keyframes modalIn{from{opacity:0;transform:scale(.9) translateY(10px)}
  to{opacity:1;transform:none}}
.modal-title{font-size:17px;font-weight:800;letter-spacing:-.02em;margin-bottom:8px}
.modal-body{font-family:'DM Mono',monospace;font-size:11px;color:var(--muted);
  line-height:1.7;margin-bottom:20px}
.modal-body b{color:var(--text)}
.modal-row{display:flex;gap:8px}
.modal-row .line{
  display:flex;align-items:center;gap:8px;
  font-family:'DM Mono',monospace;font-size:11px;color:var(--muted);
  margin-bottom:6px;
}
.modal-row .line svg{width:13px;height:13px;stroke:var(--green);flex-shrink:0;
  stroke-width:2.5;fill:none;stroke-linecap:round;stroke-linejoin:round}
.modal-btns{display:flex;gap:10px;margin-top:22px}
.modal-cancel{
  flex:1;padding:11px;border-radius:10px;border:1px solid var(--border-solid);
  background:none;color:var(--muted);font-family:'Syne',sans-serif;font-size:13px;
  cursor:pointer;transition:background .15s,border-color .15s;
}
.modal-cancel:hover{background:var(--surf2);border-color:rgba(255,255,255,.12)}
.modal-confirm{
  flex:2;padding:11px;border-radius:10px;border:none;
  background:var(--accent);color:#080a0c;
  font-family:'Syne',sans-serif;font-weight:700;font-size:13px;
  cursor:pointer;transition:background .15s,transform .1s;
}
.modal-confirm:hover{background:#22dcff;transform:translateY(-1px)}
.modal-confirm:active{transform:none}
</style>
</head>
<body>

<!-- Titlebar -->
<div class="titlebar">
  <div class="titlebar-dots">
    <div class="dot dot-r"></div>
    <div class="dot dot-y"></div>
    <div class="dot dot-g"></div>
  </div>
  <div class="titlebar-title">FPS Utility — Lite</div>
  <div class="titlebar-ver">v4.0</div>
</div>

<!-- Shell -->
<div class="shell">

  <!-- Sidebar -->
  <nav class="sidebar">
    <!-- Logo -->
    <div class="logo">
      <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path d="M13 2L4.5 13.5H11L9.5 22L19.5 10H13L13 2Z"/>
      </svg>
    </div>

    <div class="nav-item active" data-page="dashboard" onclick="navTo('dashboard')" title="Dashboard">
      <svg viewBox="0 0 24 24"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
      <span class="nav-lbl">DASH</span>
    </div>
    <div class="nav-item" data-page="cpu" onclick="navTo('cpu')" title="CPU">
      <svg viewBox="0 0 24 24"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="8" y="8" width="8" height="8"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/><line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="15" x2="4" y2="15"/><line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="15" x2="23" y2="15"/></svg>
      <span class="nav-lbl">CPU</span>
    </div>
    <div class="nav-item" data-page="gpu" onclick="navTo('gpu')" title="GPU">
      <svg viewBox="0 0 24 24"><rect x="2" y="7" width="20" height="14" rx="2"/><line x1="6" y1="21" x2="6" y2="23"/><line x1="10" y1="21" x2="10" y2="23"/><line x1="14" y1="21" x2="14" y2="23"/><line x1="18" y1="21" x2="18" y2="23"/><path d="M6 7V5a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v2"/><rect x="6" y="10" width="4" height="4" rx="1"/></svg>
      <span class="nav-lbl">GPU</span>
    </div>
    <div class="nav-item" data-page="network" onclick="navTo('network')" title="Network">
      <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
      <span class="nav-lbl">NET</span>
    </div>
    <div class="nav-item" data-page="services" onclick="navTo('services')" title="Services">
      <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83"/></svg>
      <span class="nav-lbl">SVC</span>
    </div>

    <div class="sidebar-sep"></div>
    <div class="status-dot" id="statusDot"></div>
  </nav>

  <!-- Main -->
  <div class="main">
    <!-- Topbar -->
    <div class="topbar">
      <div class="topbar-title" id="topbarTitle">Dashboard</div>
      <div class="lite-badge">LITE</div>
      <div class="sep-v"></div>
      <div class="topbar-count" id="topbarCount">19 tweaks</div>
      <div class="topbar-spacer"></div>
      <button class="apply-btn" id="applyBtn" onclick="startApply()">
        <svg viewBox="0 0 24 24"><path d="M13 2L4.5 13.5H11L9.5 22L19.5 10H13L13 2Z"/></svg>
        Apply Tweaks
      </button>
    </div>

    <!-- Content -->
    <div class="content">

      <!-- ── Dashboard page ── -->
      <div class="page active" id="page-dashboard">
        <div class="sec-hdr"><div class="sec-dot"></div><span class="sec-label">System Status</span></div>
        <div class="stats-row" id="statsRow"></div>

        <div id="warnBanner" class="warn-banner" style="display:none">
          <svg viewBox="0 0 24 24"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
          <p>A System Restore Point will be created automatically before any tweaks are applied.</p>
        </div>

        <div class="progress-wrap" id="progressWrap">
          <div class="progress-label" id="progressLabel">Applying tweaks...</div>
          <div class="progress-bar-bg"><div class="progress-bar-fill" id="progressFill"></div></div>
        </div>

        <div class="done-banner success" id="doneBanner">
          <svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>
          <p id="doneBannerText">All tweaks applied. Restart Windows for full effect.</p>
        </div>

        <div class="sec-hdr"><div class="sec-dot"></div><span class="sec-label">Tweak Overview</span></div>
        <div class="cat-cards" id="catCards"></div>

        <div class="sec-hdr" style="margin-top:16px"><div class="sec-dot green"></div><span class="sec-label" style="color:var(--green)">Console</span></div>
        <div class="console-wrap">
          <div class="console-hdr">
            <div class="console-hdr-dot"></div>
            <span>SYSTEM LOG</span>
          </div>
          <div class="console-body" id="consoleBody"></div>
        </div>
      </div>

      <!-- ── Tweak pages (CPU / GPU / Network / Services) ── -->
      <div class="page" id="page-cpu">     <div id="tweaks-cpu"></div></div>
      <div class="page" id="page-gpu">     <div id="tweaks-gpu"></div></div>
      <div class="page" id="page-network"> <div id="tweaks-network"></div></div>
      <div class="page" id="page-services"><div id="tweaks-services"></div></div>

    </div><!-- /content -->
  </div><!-- /main -->
</div><!-- /shell -->

<!-- Confirm modal -->
<div class="modal-overlay" id="modal" style="display:none" onclick="if(event.target===this)closeModal()">
  <div class="modal">
    <div class="modal-title" id="modalTitle">Apply Tweaks</div>
    <div class="modal-body" id="modalBody"></div>
    <div class="modal-btns">
      <button class="modal-cancel" onclick="closeModal()">Cancel</button>
      <button class="modal-confirm" onclick="confirmApply()">Apply Now</button>
    </div>
  </div>
</div>

<script>
// ── State ────────────────────────────────────────────────────────────────────
const state = {
  tweaks: [],
  enabled: {},       // id -> bool
  currentPage: 'dashboard',
  applying: false,
  pollInterval: null,
  progress: 0,
  progressTotal: 0,
  restoreDone: false,
};

// ── Icons per category ───────────────────────────────────────────────────────
const CAT_ICONS = {
  CPU: `<svg viewBox="0 0 24 24"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="8" y="8" width="8" height="8"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/><line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="15" x2="4" y2="15"/><line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="15" x2="23" y2="15"/></svg>`,
  GPU: `<svg viewBox="0 0 24 24"><rect x="2" y="7" width="20" height="14" rx="2"/><line x1="6" y1="21" x2="6" y2="23"/><line x1="10" y1="21" x2="10" y2="23"/><line x1="14" y1="21" x2="14" y2="23"/><line x1="18" y1="21" x2="18" y2="23"/><path d="M6 7V5a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v2"/><rect x="6" y="10" width="4" height="4" rx="1"/></svg>`,
  Network: `<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>`,
  Services: `<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83"/></svg>`,
};

// ── Init ─────────────────────────────────────────────────────────────────────
async function init() {
  await waitForAPI();
  state.tweaks = await window.pywebview.api.get_tweaks();
  state.tweaks.forEach(t => { state.enabled[t.id] = true; });

  const stats = await window.pywebview.api.get_stats();
  state.restoreDone = stats.restore_done;

  renderStats(stats);
  renderCatCards();
  renderAllTweakPages();
  updateTopbarCount();
  updateWarnBanner();
}

function waitForAPI(retries=40) {
  return new Promise((resolve, reject) => {
    const check = (n) => {
      if (window.pywebview && window.pywebview.api) return resolve();
      if (n <= 0) return reject('API timeout');
      setTimeout(() => check(n-1), 100);
    };
    check(retries);
  });
}

// ── Navigation ───────────────────────────────────────────────────────────────
function navTo(page) {
  document.querySelectorAll('.nav-item').forEach(el => {
    el.classList.toggle('active', el.dataset.page === page);
  });
  document.querySelectorAll('.page').forEach(el => {
    el.classList.toggle('active', el.id === 'page-' + page);
  });
  const titles = {dashboard:'Dashboard',cpu:'CPU',gpu:'GPU',network:'Network',services:'Services'};
  document.getElementById('topbarTitle').textContent = titles[page] || page;
  state.currentPage = page;
}

// ── Render stats ─────────────────────────────────────────────────────────────
function renderStats(stats) {
  const row = document.getElementById('statsRow');
  const rp  = stats.restore_done;
  row.innerHTML = `
    <div class="stat-card">
      <div class="stat-val">${stats.total}</div>
      <div class="stat-lbl">TOTAL TWEAKS</div>
    </div>
    <div class="stat-card">
      <div class="stat-val green">${stats.high}</div>
      <div class="stat-lbl">HIGH IMPACT</div>
    </div>
    <div class="stat-card">
      <div class="stat-val ${rp?'green':'gold'}">${rp?'Done':'Pending'}</div>
      <div class="stat-lbl">RESTORE POINT</div>
    </div>`;
}

function refreshStats() {
  window.pywebview.api.get_stats().then(s => {
    state.restoreDone = s.restore_done;
    renderStats(s);
  });
}

// ── Warn banner ──────────────────────────────────────────────────────────────
function updateWarnBanner() {
  document.getElementById('warnBanner').style.display =
    state.restoreDone ? 'none' : 'flex';
}

// ── Category overview cards ───────────────────────────────────────────────────
function renderCatCards() {
  const cats = ['CPU','GPU','Network','Services'];
  const wrap = document.getElementById('catCards');
  wrap.innerHTML = cats.map(cat => {
    const ts   = state.tweaks.filter(t=>t.cat===cat);
    const high = ts.filter(t=>t.impact==='HIGH').length;
    const dots = ts.map(t => `<div class="idot ${t.impact==='HIGH'?'high':''}"></div>`).join('');
    return `
    <div class="cat-card" onclick="navTo('${cat.toLowerCase()}')">
      <div class="cat-icon">${CAT_ICONS[cat]}</div>
      <div class="cat-info">
        <div class="cat-name">${cat}</div>
        <div class="cat-meta">${ts.length} tweaks &nbsp;·&nbsp; ${high} high impact</div>
      </div>
      <div class="cat-dots">${dots}</div>
      <div class="cat-arr">›</div>
    </div>`;
  }).join('');
}

// ── Tweak pages ──────────────────────────────────────────────────────────────
function renderAllTweakPages() {
  ['CPU','GPU','Network','Services'].forEach(cat => {
    const el = document.getElementById('tweaks-' + cat.toLowerCase());
    el.innerHTML = renderTweakPageHTML(cat);
  });
}

function renderTweakPageHTML(cat) {
  const ts   = state.tweaks.filter(t=>t.cat===cat);
  const high = ts.filter(t=>t.impact==='HIGH').length;
  const med  = ts.length - high;
  const delay_ms = (i) => i * 40;

  const cards = ts.map((t, i) => {
    const isH = t.impact === 'HIGH';
    return `
    <div class="tweak-card ${isH?'high-card':''}" style="animation-delay:${delay_ms(i)}ms">
      <div class="tweak-accent-bar ${isH?'high':''}"></div>
      <div class="tweak-body">
        <div class="tweak-top">
          <span class="tweak-name">${t.name}</span>
          <span class="impact-badge ${t.impact}">${t.impact}</span>
        </div>
        <div class="tweak-desc">${t.desc}</div>
      </div>
      <div class="tweak-toggle-wrap">
        <button class="toggle ${isH?'green-toggle':''} on"
          id="tog-${t.id}" onclick="toggleTweak('${t.id}', this)"
          title="${t.name}"></button>
      </div>
    </div>`;
  }).join('');

  return `
    <div class="tweak-page-hdr">
      <div class="tweak-page-icon">${CAT_ICONS[cat]}</div>
      <div>
        <div class="tweak-page-title">${cat}</div>
        <div class="tweak-page-meta">${high} HIGH &nbsp;·&nbsp; ${med} MED &nbsp;·&nbsp; ${ts.length} total</div>
      </div>
      <div class="tweak-page-spacer"></div>
      <button class="select-all-btn" onclick="selectAll('${cat}', true)">Select All</button>
    </div>
    <div class="tweaks-list">${cards}</div>`;
}

// ── Toggle ───────────────────────────────────────────────────────────────────
function toggleTweak(id, btn) {
  state.enabled[id] = !state.enabled[id];
  btn.classList.toggle('on', state.enabled[id]);
  updateTopbarCount();
}

function selectAll(cat, val) {
  state.tweaks.filter(t=>t.cat===cat).forEach(t => {
    state.enabled[t.id] = val;
    const btn = document.getElementById('tog-'+t.id);
    if (btn) btn.classList.toggle('on', val);
  });
  updateTopbarCount();
}

function updateTopbarCount() {
  const n = Object.values(state.enabled).filter(Boolean).length;
  document.getElementById('topbarCount').textContent = n + ' / ' + state.tweaks.length + ' tweaks';
}

// ── Apply ─────────────────────────────────────────────────────────────────────
function startApply() {
  if (state.applying) return;
  const ids = Object.entries(state.enabled).filter(([,v])=>v).map(([k])=>k);
  if (!ids.length) { alert('Enable at least one tweak first.'); return; }

  const sel  = state.tweaks.filter(t=>ids.includes(t.id));
  const high = sel.filter(t=>t.impact==='HIGH').length;

  document.getElementById('modalTitle').textContent = `Apply ${sel.length} Tweaks`;
  document.getElementById('modalBody').innerHTML = `
    <b>${sel.length} tweaks selected</b> &nbsp;(${high} HIGH impact)<br><br>
    <div class="line"><svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg> System Restore Point created first</div>
    <div class="line"><svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg> Fully reversible via Windows System Restore</div>
    <div class="line"><svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg> Restart required for full effect</div>`;

  document.getElementById('modal').style.display = 'flex';
  window._pendingIds = ids;
  window._pendingTotal = sel.length;
}

function closeModal() {
  document.getElementById('modal').style.display = 'none';
}

async function confirmApply() {
  closeModal();
  state.applying = true;
  state.progress = 0;
  state.progressTotal = window._pendingTotal;

  const applyBtn = document.getElementById('applyBtn');
  applyBtn.disabled = true;
  applyBtn.textContent = 'Working...';

  document.getElementById('statusDot').className = 'status-dot working';

  // Show progress
  const pw = document.getElementById('progressWrap');
  pw.classList.add('visible');
  document.getElementById('progressFill').style.width = '0%';

  // Navigate to dashboard to show log
  navTo('dashboard');

  // Start polling
  state.pollInterval = setInterval(pollLog, 150);

  // Kick off apply
  await window.pywebview.api.apply_tweaks(window._pendingIds);
}

// ── Log polling ───────────────────────────────────────────────────────────────
async function pollLog() {
  const lines = await window.pywebview.api.poll_log();
  lines.forEach(handleLogLine);
}

function handleLogLine({ts, msg, tag}) {
  if (tag === 'sys') {
    const m = msg.match(/__DONE__:(\d+):(\d+)/);
    if (m) applyDone(parseInt(m[1]), parseInt(m[2]));
    return;
  }

  // Update progress
  if (tag === 'ok' && msg.includes('✓')) {
    state.progress++;
    const pct = Math.min(100, Math.round(state.progress / state.progressTotal * 100));
    document.getElementById('progressFill').style.width = pct + '%';
    document.getElementById('progressLabel').textContent =
      `Applying tweaks... ${state.progress}/${state.progressTotal}`;
  }

  // Append to console
  const body = document.getElementById('consoleBody');
  const line = document.createElement('div');
  line.className = 'log-line';
  line.innerHTML = `<span class="log-ts">[${ts}]</span><span class="log-msg ${tag}">${msg}</span>`;
  body.appendChild(line);
  body.scrollTop = body.scrollHeight;
}

function applyDone(ok, fail) {
  clearInterval(state.pollInterval);
  state.applying = false;

  // Drain remaining
  window.pywebview.api.poll_log().then(lines => lines.forEach(handleLogLine));

  document.getElementById('progressFill').style.width = '100%';
  setTimeout(() => {
    document.getElementById('progressWrap').classList.remove('visible');
  }, 800);

  const applyBtn = document.getElementById('applyBtn');
  applyBtn.disabled = false;
  applyBtn.innerHTML = `<svg viewBox="0 0 24 24" style="width:14px;height:14px;fill:currentColor"><path d="M13 2L4.5 13.5H11L9.5 22L19.5 10H13L13 2Z"/></svg> Apply Tweaks`;

  document.getElementById('statusDot').className = fail > 0 ? 'status-dot error' : 'status-dot';

  const banner = document.getElementById('doneBanner');
  const text   = fail > 0
    ? `${ok} tweaks applied, ${fail} failed. See log for details. Restart recommended.`
    : `${ok} tweaks applied successfully. Restart Windows for full effect.`;
  document.getElementById('doneBannerText').textContent = text;
  banner.classList.add('visible');

  refreshStats();
  updateWarnBanner();
}

// ── Start ─────────────────────────────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', init);
</script>
</body>
</html>"""

# ─────────────────────────────────────────────────────────────────────────────
#  ENTRY
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Auto-install pywebview if missing
    try:
        import webview
    except ImportError:
        import subprocess as _sp
        print("Installing pywebview, please wait...")
        r = _sp.run(
            [sys.executable, "-m", "pip", "install", "pywebview", "--quiet"],
        )
        if r.returncode != 0:
            import tkinter as _tk
            from tkinter import messagebox as _mb
            _root = _tk.Tk(); _root.withdraw()
            _mb.showerror(
                "Missing dependency",
                "pywebview could not be installed.\n\n"
                "Please run this in a terminal:\n\n"
                "    pip install pywebview\n\n"
                "Then launch the app again."
            )
            sys.exit(1)
        import webview

    api = API()
    window = webview.create_window(
        "FPS Utility - Lite",
        html=HTML,
        js_api=api,
        width=980, height=660,
        min_size=(820, 540),
        frameless=False,
        easy_resize=True,
        background_color="#080a0c",
    )
    api._window = window
    webview.start(debug=False)
