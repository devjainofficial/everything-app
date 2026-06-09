# gateway/start-gateway.ps1
# Starts the LiteLLM gateway reproducibly. From the PROJECT ROOT, run:
#     .\gateway\start-gateway.ps1
# It runs in the FOREGROUND (you'll see live logs); press Ctrl+C to stop it.
# Open a second terminal for other work while this one holds the gateway.

$ErrorActionPreference = 'Stop'

# 1. Force UTF-8 so LiteLLM's Unicode startup banner doesn't crash on Windows' legacy cp1252 encoding.
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'

# 2. Load .env into THIS process's environment, so the `os.environ/...` refs in config.yaml resolve.
#    We print only the variable NAMES — never the secret values.
Get-Content (Join-Path $PSScriptRoot '..\.env') | ForEach-Object {
  $line = $_.Trim()
  if ($line -and -not $line.StartsWith('#') -and $line.Contains('=')) {
    $idx  = $line.IndexOf('=')
    $name = $line.Substring(0, $idx).Trim()
    $val  = $line.Substring($idx + 1).Trim()
    Set-Item -Path "env:$name" -Value $val
    Write-Host "loaded env: $name"
  }
}

# 3. LiteLLM wants the Azure model expressed as 'azure/<deployment>'. Compose it from the deployment name
#    so the config can just say `model: os.environ/AZURE_MODEL`.
$env:AZURE_MODEL = "azure/$($env:AZURE_DEPLOYMENT_NAME)"

# 4. If a previous gateway is still bound to port 4000, stop it first (avoids "address in use").
try {
  (Get-NetTCPConnection -LocalPort 4000 -State Listen -ErrorAction Stop) |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
} catch { }

# 5. Launch the proxy. It reads gateway/config.yaml and serves an OpenAI-compatible API on :4000.
$litellm = Join-Path $PSScriptRoot '..\.venv\Scripts\litellm.exe'
& $litellm --config (Join-Path $PSScriptRoot 'config.yaml') --port 4000
