# launcher.ps1 - Menu semplice per AppFoto
# Da lanciare con AvviaAppFoto.bat (doppio click) o con: .\launcher.ps1

$ErrorActionPreference = "Stop"
$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "Ambiente virtuale non trovato. Lancia prima setup.ps1" -ForegroundColor Red
    Read-Host "Premi Invio per uscire"
    exit 1
}

function Show-Menu {
    Write-Host "`n================ AppFoto ================" -ForegroundColor Cyan
    Write-Host " 1 - Cerca foto duplicate"
    Write-Host " 2 - Migliora foto (esposizione/contrasto/nitidezza)"
    Write-Host " 3 - Crea slideshow da foto"
    Write-Host " 4 - Unisci video"
    Write-Host " 0 - Esci"
    Write-Host "=========================================" -ForegroundColor Cyan
}

do {
    Show-Menu
    $choice = Read-Host "Scegli un'opzione"

    switch ($choice) {
        '1' {
            $folder = Read-Host "Cartella con le foto"
            & $venvPython (Join-Path $PSScriptRoot "main.py") duplicates $folder
        }
        '2' {
            $inputPath = Read-Host "Cartella foto in ingresso"
            $output = Read-Host "Cartella foto in uscita"
            & $venvPython (Join-Path $PSScriptRoot "main.py") enhance --input $inputPath --output $output
        }
        '3' {
            $inputPath = Read-Host "Cartella foto"
            $output = Read-Host "Nome del video da creare (es. video.mp4)"
            $music = Read-Host "File musica sottofondo (lascia vuoto per nessuna)"
            if ($music.Trim()) {
                & $venvPython (Join-Path $PSScriptRoot "main.py") slideshow --input $inputPath --output $output --music $music
            } else {
                & $venvPython (Join-Path $PSScriptRoot "main.py") slideshow --input $inputPath --output $output
            }
        }
        '4' {
            $inputPath = Read-Host "Cartella con i video"
            $output = Read-Host "Nome del video unito (es. finale.mp4)"
            & $venvPython (Join-Path $PSScriptRoot "main.py") merge --input $inputPath --output $output
        }
        '0' { exit }
        default { Write-Host "Scelta non valida, riprova." -ForegroundColor Yellow }
    }

    Write-Host ""
    Read-Host "Premi Invio per tornare al menu"
} while ($true)
