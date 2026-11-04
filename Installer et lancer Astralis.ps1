$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$url = "http://127.0.0.1:8766/index.html"
$healthUrl = "http://127.0.0.1:8766/health"

function Test-AstralisServer {
    try {
        $response = Invoke-WebRequest -Uri $healthUrl -TimeoutSec 2 -UseBasicParsing
        return ($response.StatusCode -eq 200)
    } catch { return $false }
}

function Find-AstralisPython {
    $candidates = @()
    if ($env:LOCALAPPDATA) {
        $candidates += (Join-Path $env:LOCALAPPDATA "Programs/Astralis/Python314/python.exe")
        $candidates += (Join-Path $env:LOCALAPPDATA "Programs/Astralis/Python313/python.exe")
    }
    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            & $candidate -c "import sys; raise SystemExit(sys.version_info < (3,10))" 2>$null
            if ($LASTEXITCODE -eq 0) { return $candidate }
        }
    }
    foreach ($commandName in @("py", "python")) {
        $command = Get-Command $commandName -ErrorAction SilentlyContinue
        if ($command) {
            if ($commandName -eq "py") { & $command.Source -3 -c "import sys; raise SystemExit(sys.version_info < (3,10))" 2>$null }
            else { & $command.Source -c "import sys; raise SystemExit(sys.version_info < (3,10))" 2>$null }
            if ($LASTEXITCODE -eq 0) { return $command.Source }
        }
    }
    return $null
}

function Add-AstralisShortcut {
    try {
        $desktop = [Environment]::GetFolderPath("Desktop")
        $shortcut = (New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $desktop "Astralis.lnk"))
        $shortcut.TargetPath = Join-Path $root "Installer et lancer Astralis.bat"
        $shortcut.WorkingDirectory = $root
        $shortcut.Description = "Lancer Astralis"
        $shortcut.IconLocation = "$env:SystemRoot\System32\shell32.dll,220"
        $shortcut.Save()
    } catch { Write-Host "Création du raccourci Bureau indisponible; le fichier BAT reste utilisable." }
}

try {
    if (-not (Test-AstralisServer)) {
        $python = Find-AstralisPython
        if (-not $python) {
            Write-Host "Installation de Python 3.14.10 dans le profil Windows..."
            $installer = Join-Path $env:TEMP "astralis-python-3.14.10-amd64.exe"
            $target = Join-Path $env:LOCALAPPDATA "Programs/Astralis/Python314"
            Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.14.10/python-3.14.10-amd64.exe" -OutFile $installer
            $process = Start-Process -FilePath $installer -ArgumentList @("/quiet", "InstallAllUsers=0", "PrependPath=0", "Include_launcher=0", "Include_test=0", "Include_pip=0", "TargetDir=$target") -Wait -PassThru
            if ($process.ExitCode -ne 0) { throw "Installation de Python échouée (code $($process.ExitCode))." }
            $python = Join-Path $target "python.exe"
            if (-not (Test-Path $python)) { throw "Python n’a pas été installé correctement." }
        }
        $listener = Get-NetTCPConnection -LocalPort 8766 -State Listen -ErrorAction SilentlyContinue
        if ($listener) { throw "Le port 8766 est déjà occupé; ferme l’instance Astralis puis réessaie." }
        Start-Process -FilePath $python -ArgumentList "server.py" -WorkingDirectory $root -WindowStyle Hidden
        $ready = $false
        for ($attempt = 0; $attempt -lt 40; $attempt++) {
            Start-Sleep -Milliseconds 500
            if (Test-AstralisServer) { $ready = $true; break }
        }
        if (-not $ready) { throw "Le serveur local ne répond pas. Relance le fichier BAT." }
    }
    Add-AstralisShortcut
    $edgePaths = @()
    if (${env:ProgramFiles(x86)}) { $edgePaths += (Join-Path ${env:ProgramFiles(x86)} "Microsoft/Edge/Application/msedge.exe") }
    if ($env:ProgramFiles) { $edgePaths += (Join-Path $env:ProgramFiles "Microsoft/Edge/Application/msedge.exe") }
    if ($env:LOCALAPPDATA) { $edgePaths += (Join-Path $env:LOCALAPPDATA "Microsoft/Edge/Application/msedge.exe") }
    $edge = $edgePaths | Where-Object { Test-Path $_ } | Select-Object -First 1
    if ($edge) { Start-Process -FilePath $edge -ArgumentList "--app=$url" }
    else { Start-Process $url }
    Write-Host "Astralis est lancé. Le raccourci est sur le Bureau."
} catch {
    Write-Host "Erreur : $($_.Exception.Message)" -ForegroundColor Red
    Read-Host "Appuie sur Entrée pour fermer"
    exit 1
}
