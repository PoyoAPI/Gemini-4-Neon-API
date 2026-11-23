Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")

Write-Host "Checking Node.js syntax"
Get-ChildItem -LiteralPath $Root -Recurse -Filter *.mjs -File | Where-Object { $_.FullName -notmatch "[\\/](node_modules|\.git)[\\/]" } | ForEach-Object {
  & node --check $_.FullName
  if ($LASTEXITCODE -ne 0) { throw "Node syntax failed: $($_.FullName)" }
}

Write-Host "Checking missing-key behavior"
$oldKey = $env:POYO_API_KEY
Remove-Item Env:\POYO_API_KEY -ErrorAction SilentlyContinue
try {
  $previousErrorAction = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  $output = (& node (Join-Path $Root "node/index.mjs") 2>&1 | Out-String)
  $nodeExitCode = $LASTEXITCODE
  $ErrorActionPreference = $previousErrorAction
  if ($nodeExitCode -eq 0 -or $output -notmatch "POYO_API_KEY") { throw "Node example must fail safely without POYO_API_KEY" }
} finally {
  $ErrorActionPreference = "Stop"
  if ($null -ne $oldKey) { $env:POYO_API_KEY = $oldKey }
}

Write-Host "Checking request payloads"
Get-ChildItem -LiteralPath (Join-Path $Root "payloads") -Recurse -Filter *.json -File | ForEach-Object {
  $payload = Get-Content -LiteralPath $_.FullName -Raw | ConvertFrom-Json
  $names = $payload.PSObject.Properties.Name
  if ($names -contains "contents") {
    if (@($payload.contents).Count -lt 1) { throw "contents must not be empty in $($_.Name)" }
    $config = $payload.PSObject.Properties["generationConfig"]
    if ($null -ne $config -and $null -ne $config.Value.PSObject.Properties["thinkingConfig"]) {
      $level = $config.Value.thinkingConfig.thinkingLevel
      if (@("low", "medium", "high", "xhigh") -notcontains $level) { throw "Unexpected thinkingLevel in $($_.Name): $level" }
    }
  } elseif ($names -contains "messages") {
    if ($payload.model -ne "gemini-4-neon") { throw "Unexpected model in $($_.Name): $($payload.model)" }
  } else {
    throw "Payload must use messages (Chat Completions) or contents (Gemini Native): $($_.Name)"
  }
}

Write-Host "Checking Python example"
& python -m py_compile (Join-Path $Root "python/generate.py")
if ($LASTEXITCODE -ne 0) { throw "Python syntax failed" }
$oldKey = $env:POYO_API_KEY
Remove-Item Env:\POYO_API_KEY -ErrorAction SilentlyContinue
try {
  $ErrorActionPreference = "Continue"
  $output = (& python (Join-Path $Root "python/generate.py") 2>&1 | Out-String)
  $pythonExitCode = $LASTEXITCODE
  $ErrorActionPreference = "Stop"
  if ($pythonExitCode -eq 0 -or $output -notmatch "POYO_API_KEY") { throw "Python example must fail safely without POYO_API_KEY" }
} finally {
  $ErrorActionPreference = "Stop"
  if ($null -ne $oldKey) { $env:POYO_API_KEY = $oldKey }
}

Write-Host "Scanning for committed secrets"
$files = Get-ChildItem -LiteralPath $Root -Recurse -File | Where-Object { $_.FullName -notmatch "[\\/](node_modules|\.git)[\\/]" }
foreach ($file in $files) {
  $text = [IO.File]::ReadAllText($file.FullName)
  if ($text -match "poyo_[A-Za-z0-9_-]{20,}") { throw "Possible API key in $($file.FullName)" }
}
Write-Host "All checks passed."
exit 0
