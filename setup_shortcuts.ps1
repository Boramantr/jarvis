$ws = New-Object -ComObject WScript.Shell

# Desktop shortcut
$desktop = [Environment]::GetFolderPath('Desktop')
$shortcut = $ws.CreateShortcut("$desktop\JARVIS.lnk")
$shortcut.TargetPath = "C:\Users\borao\OneDrive\Masaüstü\Mark-XXXIX-main\JARVIS.bat"
$shortcut.WorkingDirectory = "C:\Users\borao\OneDrive\Masaüstü\Mark-XXXIX-main"
$shortcut.WindowStyle = 7
$shortcut.Description = "JARVIS AI Assistant"
$shortcut.Save()
Write-Host "Desktop shortcut created!"

# Startup entry
$startup = $ws.SpecialFolders("Startup")
$startupShortcut = $ws.CreateShortcut("$startup\JARVIS.lnk")
$startupShortcut.TargetPath = "C:\Users\borao\OneDrive\Masaüstü\Mark-XXXIX-main\JARVIS.bat"
$startupShortcut.WorkingDirectory = "C:\Users\borao\OneDrive\Masaüstü\Mark-XXXIX-main"
$startupShortcut.WindowStyle = 7
$startupShortcut.Description = "JARVIS Auto Start"
$startupShortcut.Save()
Write-Host "Startup entry created!"
