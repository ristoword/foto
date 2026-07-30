# setup.ps1 - Prepara l'ambiente virtuale e installa le dipendenze per AppFoto
# Eseguire da PowerShell nella cartella del progetto.
# Richiede Python e FFmpeg installati e presenti nel PATH.

$ErrorActionPreference = "Stop"
$venvPath = ".venv"

function Find-Python {
    $candidates = @("python", "py", "python3")
    foreach ($c in $candidates) {
        $exe = Get-Command $c -ErrorAction SilentlyContinue
        if ($exe) { return $c }
    }
    return $null
}

$pythonCmd = Find-Python
if (-not $pythonCmd) {
    Write-Host "ERRORE: Python non trovato nel PATH. Installa Python da https://www.python.org/downloads/" -ForegroundColor Red
    exit 1
}

if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    Write-Host "AVVISO: FFmpeg non trovato nel PATH. Scaricalo da https://ffmpeg.org/download.html e aggiungilo al PATH prima di usare slideshow/merge." -ForegroundColor Yellow
}

Write-Host "Trovato Python: $pythonCmd" -ForegroundColor Green

if (Test-Path $venvPath) {
    Write-Host "Rilevato ambiente esistente: $venvPath" -ForegroundColor Cyan
} else {
    Write-Host "Creazione ambiente virtuale..." -ForegroundColor Cyan
    & $pythonCmd -m venv $venvPath
}

Write-Host "Installazione/aggiornamento dipendenze..." -ForegroundColor Cyan
& "$venvPath\Scripts\pip.exe" install --upgrade pip
& "$venvPath\Scripts\pip.exe" install -r requirements.txt

Write-Host "Verifica import base..." -ForegroundColor Cyan
& "$venvPath\Scripts\python.exe" -c "import PIL, imagehash, cv2, numpy; print('Import OK')"

Write-Host "Setup completato. Attiva il venv con: .venv\Scripts\Activate.ps1" -ForegroundColor Green
