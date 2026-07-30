Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")

folder = FSO.GetParentFolderName(WScript.ScriptFullName)
cmd = "powershell -WindowStyle Hidden -ExecutionPolicy Bypass -File """ & folder & "\launch.ps1"""

WshShell.Run cmd, 0, False

Set WshShell = Nothing
Set FSO = Nothing
