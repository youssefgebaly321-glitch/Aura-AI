# Aura Local Startup Instructions

Use this method when you want Aura to run without leaving a terminal window open.

## Current Working Startup Method

Run this from PowerShell:

```powershell
Start-Process -FilePath "C:\Users\Youssef Gebaly\Aura-AI\venv\Scripts\python.exe" -ArgumentList "main.py" -WorkingDirectory "C:\Users\Youssef Gebaly\Aura-AI" -WindowStyle Hidden -RedirectStandardOutput "C:\Users\Youssef Gebaly\Aura-AI\aura-start.out.log" -RedirectStandardError "C:\Users\Youssef Gebaly\Aura-AI\aura-start.err.log"
```

This starts Aura with:

- no visible launcher terminal
- logs written to `aura-start.out.log` and `aura-start.err.log`
- the Aura app window still visible and usable

## Required Local Setting

Keep this in `.env` if you want the app window to show when it starts:

```text
START_IN_STEALTH_MODE=false
```

If the window is running but not visible, press:

```text
Alt+Z
```
## Background Mode

Closing the Aura window now hides it instead of stopping the app. Aura continues to
run in the background, and you can bring it back with `Alt+Z` or the Aura icon in
the Windows notification area. To stop it completely, right-click the tray icon and
choose **Quit Aura**.

## Startup Crash Fix

`main.py` includes a UTF-8 stdout/stderr configuration near the top:

```python
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
```

Keep this patch. Without it, hidden startup can fail on Windows when Aura prints emoji logs before the GUI opens.

## If Dependencies Are Missing

First run the repo launcher once:

```powershell
cd "C:\Users\Youssef Gebaly\Aura-AI"
.\run.bat
```

After `venv` is created and requirements are installed, use the terminal-free `Start-Process` command above for normal launches.

