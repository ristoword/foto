$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$log = Join-Path $root "launch.log"

if (Test-Path $log) { Remove-Item $log -Force }

function Write-Log($msg) {
    Add-Content -Path $log -Value "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $msg" -ErrorAction SilentlyContinue
}

$streamlit = Join-Path $root ".venv\Scripts\streamlit.exe"

try {
    if (-not (Test-Path $streamlit)) {
        throw "Streamlit non trovato in .venv\Scripts\streamlit.exe. Lancia setup.ps1."
    }

    Write-Log "Avvio server Streamlit in background..."
    $proc = Start-Process -FilePath $streamlit `
        -ArgumentList "run","dashboard.py","--server.headless","true","--browser.gatherUsageStats","false" `
        -WindowStyle Hidden -WorkingDirectory $root -PassThru

    Write-Log "Processo Streamlit avviato con PID $($proc.Id)"

    $url = "http://localhost:8501"
    $started = $false
    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep -Seconds 1
        try {
            $resp = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
            if ($resp.StatusCode -eq 200) { $started = $true; break }
        } catch {}
    }

    if (-not $started) {
        throw "Server Streamlit non raggiungibile entro 30 secondi. Controlla launch.log."
    }

    Write-Log "Server attivo. Apertura browser su $url"
    Start-Process $url
} catch {
    Write-Log "ERRORE: $_"
    exit 1
}
