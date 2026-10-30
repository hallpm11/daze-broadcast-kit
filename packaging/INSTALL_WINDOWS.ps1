# Daze Broadcast Kit v1.3: copies static OBS assets and the prebuilt local bridge.
# This is intentionally limited to the current user's Videos directory.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$exe = Join-Path $root 'DazeTelemetry.exe'
$assets = Join-Path $root 'assets'
$template = Join-Path (Join-Path $root 'templates') 'DAZE_UNIVERSAL.template.json'
if (-not (Test-Path -LiteralPath $exe)) {
    throw 'DazeTelemetry.exe missing. Download the compiled Windows ZIP from GitHub Actions/Releases; this source checkout is NOT the Windows distribution.'
}
if (-not (Test-Path -LiteralPath $template) -or -not (Test-Path -LiteralPath $assets)) {
    throw 'Package incomplete. Extract the entire ZIP before installing.'
}
$install = Join-Path (Join-Path $env:USERPROFILE 'Videos') 'DazeBroadcastKitUniversal'
$targetAssets = Join-Path $install 'assets'
New-Item -ItemType Directory -Force -Path $install, $targetAssets | Out-Null
Copy-Item -LiteralPath $exe -Destination (Join-Path $install 'DazeTelemetry.exe') -Force
Copy-Item -Path (Join-Path $assets '*') -Destination $targetAssets -Recurse -Force
Copy-Item -LiteralPath (Join-Path $root 'START_DAZE.cmd') -Destination (Join-Path $install 'START_DAZE.cmd') -Force
$src = [System.IO.File]::ReadAllText($template)
$resolved = $src.Replace('__ASSET_ROOT__', $targetAssets.Replace('\', '/'))
if ($resolved.Contains('__ASSET_ROOT__')) { throw 'Failed to substitute OBS asset paths.' }
$null = $resolved | ConvertFrom-Json
$outfile = Join-Path $install 'DAZE_OBS_MASTER_v1.3_IMPORT.json'
$utf8 = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($outfile, $resolved, $utf8)
Write-Host ''
Write-Host 'DAZE BROADCAST KIT v1.3 INSTALLED' -ForegroundColor Green
Write-Host ('Local launch: ' + (Join-Path $install 'START_DAZE.cmd'))
Write-Host ('OBS import:   ' + $outfile)
Write-Host 'NEXT: Run START_DAZE.cmd; open OBS > Scene Collection > Import; select the import JSON.'
Write-Host 'Then choose Driver POV or Broadcast Team, and configure iRacing Game Capture once.'
Write-Host 'Data hides if iRacing is disconnected. No event details or credentials are requested.'
