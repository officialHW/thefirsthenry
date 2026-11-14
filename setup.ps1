# Set up Henry on a new Windows computer. Double-click setup.bat, which runs this file.
# It installs Hermes Agent with its official installer, puts back Henry's memory, skills and
# settings from the bundle, and asks for your Gemini key (typing stays hidden).
$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot
$env:HERMES_HOME = Join-Path $PSScriptRoot "hermes"

Write-Host ""
Write-Host "This will download and install Hermes Agent (about 1-2 GB) from the official site:"
Write-Host "    https://hermes-agent.nousresearch.com/install.ps1"
$ok = Read-Host "Go ahead? Type y and press Enter"
if ($ok -ne "y" -and $ok -ne "Y") { Write-Host "Stopped. Nothing was installed."; exit 1 }

$installer = [scriptblock]::Create((Invoke-RestMethod https://hermes-agent.nousresearch.com/install.ps1))
& $installer -HermesHome $env:HERMES_HOME -InstallDir (Join-Path $env:HERMES_HOME "hermes-agent") `
    -SkipBrowser -SkipComputerUse -NonInteractive

$py = Get-ChildItem -Path (Join-Path $env:HERMES_HOME "tools") -Filter "python.exe" -Recurse -Depth 2 -ErrorAction SilentlyContinue |
    Select-Object -Last 1 -ExpandProperty FullName
if (-not $py) { $py = "python" }

if (Test-Path "hermes-data") {
    Write-Host "Putting back Henry's memory, skills and settings..."
    & $py tools\restore.py
}

Write-Host ""
Write-Host "Now your Gemini key (free from https://aistudio.google.com/apikey)."
Write-Host "Paste it and press Enter. Nothing shows on screen while you paste: that is on purpose."
Write-Host "Using a different AI service? Just press Enter here and pick it afterwards (see README, 'Choose his AI service')."
& $py tools\set_key.py
if ($LASTEXITCODE -ne 0) {
    & $py tools\set_key.py --link-only
    Write-Host "No Gemini key saved. Before starting him, choose an AI service with the 'hermes model' command (see README)."
}

Write-Host ""
if (Get-Command npm -ErrorAction SilentlyContinue) {
    $ov = Read-Host "Also install the desktop overlay (Electron, about 200 MB, lets Henry walk on top of your whole screen)? [y/N]"
    if ($ov -eq "y" -or $ov -eq "Y") { Push-Location overlay; npm ci --no-fund --no-audit; npx electron --version; Pop-Location }
} else {
    Write-Host "(Optional: install Node.js from nodejs.org, then run this again to get the desktop overlay.)"
}

Write-Host ""
Write-Host "All set. Start Henry by double-clicking start.bat."
Write-Host "For Henry on top of your whole desktop: start-overlay.bat (needs the overlay installed)."
