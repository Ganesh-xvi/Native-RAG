# Local development server (Windows-friendly — uses uvicorn)

$env:PYTHONUNBUFFERED = "1"

Set-Location $PSScriptRoot\..



if (Test-Path ".env") {

    Get-Content ".env" | ForEach-Object {

        if ($_ -match '^\s*([^#][^=]+)=(.*)$') {

            [System.Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), "Process")

        }

    }

}



$host_ = if ($env:API_HOST) { $env:API_HOST } else { "0.0.0.0" }

$port = if ($env:API_PORT) { $env:API_PORT } else { "8000" }

$logLevel = if ($env:LOG_LEVEL) { $env:LOG_LEVEL.ToLower() } else { "info" }



Write-Host "Starting uvicorn on ${host_}:${port} (LOG_LEVEL=$logLevel) ..."

Write-Host "Logs will appear below. Press Ctrl+C to stop."

python -m uvicorn src.api.main:app --host $host_ --port $port --reload --log-level $logLevel

