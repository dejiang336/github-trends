' Hidden launcher for auto_run.bat
' ASCII only, no BOM (WSH reads .vbs as ANSI -- a UTF-8 BOM is a syntax error).
'
' Why this exists:
'   The scheduled task used to run "cmd.exe /c auto_run.bat" directly, which
'   opens a VISIBLE console window. Closing that window kills the crawler with
'   STATUS_CONTROL_C_EXIT (0xC000013A). On 2026-09-13 and 2026-09-27 exactly
'   that happened and the week's snapshot was lost.
'   wscript.exe is a GUI-subsystem binary, so it allocates no console itself,
'   and Run(..., 0, ...) creates the child console with SW_HIDE.
'
' bWaitOnReturn must be True:
'   With False, wscript exits 0 immediately, Task Scheduler sees success before
'   the crawl finishes, and restart-on-failure never fires. The 3rd argument
'   being True is what forwards the real exit code to Task Scheduler.

Option Explicit

Dim sh, rc
Set sh = CreateObject("WScript.Shell")
sh.CurrentDirectory = "C:\Users\jd\Desktop\github-trends"
rc = sh.Run("cmd.exe /c ""C:\Users\jd\Desktop\github-trends\auto_run.bat""", 0, True)
WScript.Quit rc
