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
$Shortcut = Join-Path $Root "shared\AI Agent - Chrome.lnk"

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

# Chrome RESTORES the last window bounds from the profile, which beats --window-position on the
# command line. So after every launch we place the window explicitly: on-screen when the human
# asked for it, off-screen when the automation is running unattended.
if (-not ("AgentWin" -as [type])) {
  Add-Type @"
using System;
using System.Runtime.InteropServices;
public struct AGENT_RECT { public int Left, Top, Right, Bottom; }
public class AgentWin {
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out AGENT_RECT r);
  [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr h);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int cmd);
  [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr h, IntPtr after, int x, int y, int cx, int cy, uint flags);
}
"@
}

function Get-AgentWindowHandle {
  for ($i = 0; $i -lt 24; $i++) {
    $p = Get-AgentChrome | Select-Object -First 1
    if ($p) {
      $proc = Get-Process -Id $p.ProcessId -ErrorAction SilentlyContinue
      if ($proc -and $proc.MainWindowHandle -ne 0) { return $proc.MainWindowHandle }
    }
    Start-Sleep -Milliseconds 250
  }
  return [IntPtr]::Zero
}

function Set-AgentWindow([bool]$onScreen) {
  $h = Get-AgentWindowHandle
  if ($h -eq [IntPtr]::Zero) { return $false }
  if ($onScreen) {
    [void][AgentWin]::ShowWindow($h, 9)                                             # SW_RESTORE
    [void][AgentWin]::SetWindowPos($h, [IntPtr]::Zero, 120, 80, 1366, 900, 0x0040)  # SWP_SHOWWINDOW
  } else {
    [void][AgentWin]::SetWindowPos($h, [IntPtr]::Zero, -32000, -32000, 1280, 900, 0x0040)
    [void][AgentWin]::ShowWindow($h, 6)                                             # SW_MINIMIZE
  }
  return $true
}

function Get-AgentWindowState {
  $h = Get-AgentWindowHandle
  if ($h -eq [IntPtr]::Zero) { return "no window" }
  $r = New-Object AGENT_RECT
  [void][AgentWin]::GetWindowRect($h, [ref]$r)
  if ([AgentWin]::IsIconic($h)) { return "minimized" }
  if ($r.Left -le -30000 -or $r.Top -le -30000) { return "OFF-SCREEN" }
  return "visible at $($r.Left),$($r.Top)"
}

if ($CreateShortcut) {
  $ws = New-Object -ComObject WScript.Shell
  $s = $ws.CreateShortcut($Shortcut)
  # Target the launcher (not chrome.exe) so the window can be forced on-screen even though Chrome
  # restores old bounds; -WindowStyle Hidden keeps the console from flashing.
  $s.TargetPath = (Get-Command powershell.exe).Source
  $s.Arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$PSCommandPath`" -Visible"
  $s.WorkingDirectory = $Root
  $s.IconLocation = "$Chrome,0"
  $s.WindowStyle = 7
  $s.Description = "AI Agent - Tekify Chrome (separate data dir, automation attaches via CDP)"
  $s.Save()
  Write-Host "Created $Shortcut"
  Write-Host "Right-click it -> Pin to taskbar (Windows blocks scripted taskbar pinning)."
  Write-Host "Clicking it opens the AIProfile window on screen; automation attaches to that same browser."
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
  Write-Host "window  : $(Get-AgentWindowState)"
  if (Test-Path $Shortcut) { Write-Host "shortcut: $Shortcut" }
  return
}

if ($running -and $cdpUp) {
  Write-Host "agent Chrome already running (pid $($running.ProcessId -join ', ')) — reusing http://127.0.0.1:$Port"
  if ($Visible) { [void](Set-AgentWindow $true) }
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
  [void](Set-AgentWindow ([bool]$Visible))
  Write-Host "agent Chrome started — CDP ready at http://127.0.0.1:$Port  (window: $(Get-AgentWindowState))"
} else {
  Write-Host "agent Chrome started but CDP did not come up on port $Port — check chrome://inspect"
  exit 1
}
