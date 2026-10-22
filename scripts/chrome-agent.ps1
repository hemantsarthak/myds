<#
.SYNOPSIS
  Start, reuse or stop the dedicated AI-agent Chrome. Invisible by default.

.DESCRIPTION
  Every browser flow in this repo should share ONE persistent Chrome profile so logins (Bing
  Webmaster Tools, affiliate dashboards, Cloudflare, x402) survive between sessions and the agent
  stops opening and closing throwaway browsers.

  This launcher:
    * uses shared/chrome-agent-profile (gitignored) as the persistent profile;
    * exposes a Chrome DevTools endpoint on 127.0.0.1:9222 so scripts can ATTACH to the running
      browser instead of spawning another one (see scripts/agentbrowser.mjs);
    * keeps the window OFF-SCREEN and minimized so it never steals the human's focus. Use
      -Visible only for a captcha/KYC step the human must physically solve.
    * -CreateShortcut writes shared/chrome-agent.lnk; Windows does not let a script pin to the
      taskbar, so right-click that shortcut once and "Pin to taskbar".

.EXAMPLE
  scripts/chrome-agent.ps1                    # start (or report) the invisible agent browser
  scripts/chrome-agent.ps1 -Status
  scripts/chrome-agent.ps1 -Url "https://www.bing.com/webmasters"
  scripts/chrome-agent.ps1 -Visible -Url "https://signup.live.com"   # human-in-the-loop only
  scripts/chrome-agent.ps1 -CreateShortcut
  scripts/chrome-agent.ps1 -Stop
#>
param(
  [string]$Url,
  [switch]$Visible,
  [switch]$Status,
  [switch]$CreateShortcut,
  [switch]$Stop,
  [int]$Port = 9222
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$ProfileDir = Join-Path $Root "shared\chrome-agent-profile"
$Shortcut = Join-Path $Root "shared\chrome-agent.lnk"

$Chrome = @(
  (Join-Path $env:ProgramFiles "Google\Chrome\Application\chrome.exe"),
  (Join-Path ${env:ProgramFiles(x86)} "Google\Chrome\Application\chrome.exe"),
  (Join-Path $env:LOCALAPPDATA "Google\Chrome\Application\chrome.exe")
) | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
if (-not $Chrome) { throw "chrome.exe not found — install Chrome or set a custom path" }

New-Item -ItemType Directory -Force -Path $ProfileDir | Out-Null

function Get-AgentChrome {
  Get-CimInstance Win32_Process -Filter "Name='chrome.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -and $_.CommandLine -like "*$ProfileDir*" -and $_.CommandLine -notlike "*--type=*" }
}

function Test-Cdp {
  try {
    $r = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/json/version" -TimeoutSec 2 -UseBasicParsing
    return $r.StatusCode -eq 200
  } catch { return $false }
}

function Open-ViaCdp([string]$target) {
  $u = [uri]::EscapeDataString($target)
  try {
    Invoke-WebRequest -Uri "http://127.0.0.1:$Port/json/new?$u" -Method Put -TimeoutSec 5 -UseBasicParsing | Out-Null
    return $true
  } catch {
    try {
      Invoke-WebRequest -Uri "http://127.0.0.1:$Port/json/new?$u" -TimeoutSec 5 -UseBasicParsing | Out-Null
      return $true
    } catch { return $false }
  }
}

if ($CreateShortcut) {
  $ws = New-Object -ComObject WScript.Shell
  $s = $ws.CreateShortcut($Shortcut)
  $s.TargetPath = $Chrome
  $s.Arguments = "--user-data-dir=`"$ProfileDir`" --profile-directory=Default --remote-debugging-port=$Port --no-first-run --no-default-browser-check --start-minimized --window-position=-32000,-32000 --window-size=1280,900"
  $s.WorkingDirectory = $Root
  $s.IconLocation = "$Chrome,0"
  $s.Description = "Tekify AI agent Chrome (dedicated profile, starts invisible)"
  $s.Save()
  Write-Host "Created $Shortcut"
  Write-Host "Right-click it -> Pin to taskbar (Windows blocks scripted taskbar pinning)."
  Write-Host "After pinning, one click starts the agent browser minimized/off-screen."
  return
}

if ($Stop) {
  $procs = Get-AgentChrome
  if (-not $procs) { Write-Host "agent Chrome is not running"; return }
  foreach ($p in $procs) { Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue }
  Write-Host "stopped agent Chrome (pid $($procs.ProcessId -join ', '))"
  return
}

$running = Get-AgentChrome
$cdpUp = Test-Cdp

if ($Status) {
  Write-Host "profile : $ProfileDir"
  Write-Host "chrome  : $Chrome"
  Write-Host "running : $(if ($running) { 'yes (pid ' + ($running.ProcessId -join ', ') + ')' } else { 'no' })"
  Write-Host "cdp     : $(if ($cdpUp) { "ready at http://127.0.0.1:$Port" } else { 'not listening' })"
  Write-Host "window  : $(if ($Visible) { 'visible' } else { 'off-screen/minimized' })"
  if (Test-Path $Shortcut) { Write-Host "shortcut: $Shortcut" }
  return
}

if ($running -and $cdpUp) {
  Write-Host "agent Chrome already running (pid $($running.ProcessId -join ', ')) — reusing http://127.0.0.1:$Port"
  if ($Url) {
    if (Open-ViaCdp $Url) { Write-Host "opened tab: $Url" } else { Write-Host "could not open tab via CDP; navigate manually" }
  }
  return
}

$args = @(
  "--user-data-dir=$ProfileDir",
  "--profile-directory=Default",
  "--remote-debugging-port=$Port",
  "--no-first-run",
  "--no-default-browser-check",
  "--disable-features=Translate,ChromeWhatsNewUI,MediaRouter",
  "--disable-blink-features=AutomationControlled"
)
if ($Visible) {
  $args += @("--window-size=1366,900", "--window-position=120,80")
} else {
  # the point: never steal focus. Off-screen + minimized works even when Chrome ignores
  # --start-minimized on some Windows builds.
  $args += @("--start-minimized", "--window-position=-32000,-32000", "--window-size=1280,900")
}
if ($Url) { $args += $Url }

Start-Process -FilePath $Chrome -ArgumentList $args | Out-Null

# wait for the DevTools endpoint so callers can attach immediately
for ($i = 0; $i -lt 60; $i++) {
  Start-Sleep -Milliseconds 250
  if (Test-Cdp) { break }
}

if (Test-Cdp) {
  Write-Host "agent Chrome started — CDP ready at http://127.0.0.1:$Port  (window: $(if ($Visible) { 'VISIBLE (human-in-the-loop)' } else { 'off-screen/minimized' }))"
} else {
  Write-Host "agent Chrome started but CDP did not come up on port $Port — check chrome://inspect"
  exit 1
}
