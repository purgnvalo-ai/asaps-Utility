
FPS Utility — Lite
==================
Version 1.0.0 | Windows 10/11 | Requires Administrator

────────────────────────────────────────────────────────────
WHAT THIS DOES
────────────────────────────────────────────────────────────

Before touching anything, the app creates a System Restore
Point. Every single change can be undone in one click via
Windows System Restore (Control Panel → Recovery).

Tweaks applied:

  CPU
  ├─ High Performance Power Plan
  ├─ Disable Core Parking
  └─ Disable CPU Idle States (C-States)

  GPU
  ├─ Hardware GPU Scheduler (WDDM 2.7)
  └─ Enable Shader Cache

  Network
  └─ Disable Nagle Algorithm (TCP low-latency)

  Services
  ├─ Disable SysMain (Superfetch)
  ├─ Disable Search Indexing
  ├─ Disable Xbox Game Bar / DVR
  └─ Disable Telemetry (DiagTrack)

────────────────────────────────────────────────────────────
HOW TO BUILD THE .EXE
────────────────────────────────────────────────────────────

Requirements:
  • Python 3.9 or newer (python.org) — check "Add to PATH"
  • Windows 10 version 1903+ or Windows 11
  • Internet connection (for pip to fetch PyInstaller)

Steps:
  1. Double-click BUILD.bat
  2. Wait ~60 seconds for compilation
  3. Find your .exe in the dist\ folder

────────────────────────────────────────────────────────────
HOW TO USE
────────────────────────────────────────────────────────────

  1. Right-click "FPS Utility Lite.exe" → Run as Administrator
     (Admin rights needed to modify system settings)

  2. Toggle individual tweaks on/off using the switches
     in each category tab (CPU / GPU / Network / Services)

  3. Click "Apply Tweaks" on the Dashboard

  4. The app will:
     a) Create a System Restore Point automatically
     b) Apply all enabled tweaks one by one
     c) Show a live log of every action

  5. Restart your PC when prompted

────────────────────────────────────────────────────────────
HOW TO UNDO
────────────────────────────────────────────────────────────

  Option A — Windows System Restore
    Control Panel → Recovery → Open System Restore
    Select the restore point named "FPS Utility Lite"
    Follow the wizard. Takes ~5 minutes. Fully automated.

  Option B — Manual
    Power Plan:   powercfg /setactive SCHEME_BALANCED
    Services:     sc config SysMain start= auto && sc start SysMain
                  sc config WSearch start= delayed-auto && sc start WSearch

────────────────────────────────────────────────────────────
SAFETY
────────────────────────────────────────────────────────────

  ✓ No game files touched — undetectable by anti-cheat
  ✓ Restore point created before EVERY apply
  ✓ Open-source — main.py is fully readable
  ✓ No network calls made by the app itself

────────────────────────────────────────────────────────────
SYSTEM REQUIREMENTS
────────────────────────────────────────────────────────────

  OS:  Windows 10 (1903+) or Windows 11
  RAM: 4 GB minimum
  Rights: Administrator

────────────────────────────────────────────────────────────
