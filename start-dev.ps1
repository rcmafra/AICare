param(
    [int]$ExpoPort = 8081
)

$ErrorActionPreference = 'Stop'

if ($ExpoPort -lt 1 -or $ExpoPort -gt 65535) {
    throw "ExpoPort precisa estar entre 1 e 65535. Valor recebido: $ExpoPort"
}

$root = $PSScriptRoot
$python = Join-Path $root 'backend\.venv\Scripts\python.exe'
$backendSource = Join-Path $root 'backend\src'
$frontend = Join-Path $root 'frontend'

if (-not (Test-Path $python)) {
    throw 'Python do backend nao encontrado em backend\.venv. Crie o ambiente virtual e instale backend\src\requirements.txt.'
}
if (-not (Test-Path (Join-Path $frontend 'node_modules\.bin\expo.cmd'))) {
    throw 'Dependencias do frontend nao encontradas. Execute npm install em frontend antes de iniciar.'
}

function Test-PortAvailable([int]$Port) {
    $listener = [System.Net.Sockets.TcpListener]::new(
        [System.Net.IPAddress]::Any,
        $Port
    )
    try {
        $listener.Start()
        return $true
    }
    catch [System.Net.Sockets.SocketException] {
        return $false
    }
    finally {
        $listener.Stop()
    }
}

if (-not (Test-PortAvailable 8000)) {
    throw 'A porta 8000 ja esta ocupada. Encerre o processo que a utiliza e tente novamente.'
}

while (-not (Test-PortAvailable $ExpoPort)) {
    Write-Host "A porta Expo $ExpoPort esta ocupada; tentando a proxima."
    $ExpoPort++
    if ($ExpoPort -gt 65535) {
        throw 'Nao foi encontrada uma porta disponivel para o Expo.'
    }
}

Write-Host 'Iniciando a API local em http://localhost:8000 ...'
$backendProcess = Start-Process `
    -FilePath $python `
    -ArgumentList @(
        '-m', 'uvicorn', 'main:app',
        '--app-dir', $backendSource,
        '--host', '0.0.0.0',
        '--port', '8000',
        '--reload'
    ) `
    -WorkingDirectory $backendSource `
    -PassThru

try {
    $apiReady = $false
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        if ($backendProcess.HasExited) {
            throw 'O backend encerrou inesperadamente. Verifique a janela da API para ver o erro.'
        }

        try {
            $health = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/health' -TimeoutSec 2
            if ($health.status -eq 'ok') {
                $apiReady = $true
                break
            }
        }
        catch {
            Start-Sleep -Seconds 1
        }
    }

    if (-not $apiReady) {
        throw 'A API nao ficou pronta em 30 segundos. Verifique a janela do backend.'
    }

    Write-Host "API pronta. Iniciando o Expo na porta $ExpoPort ..."
    Push-Location $frontend
    try {
        & npx.cmd expo whoami
        if ($LASTEXITCODE -eq 0) {
            Write-Host 'Usuario ja autenticado no Expo; login ignorado.'
        }
        else {
            Write-Host 'Nenhum usuario autenticado no Expo; solicitando login.'
            & npx.cmd expo login --no-browser
            if ($LASTEXITCODE -ne 0) {
                throw "O login do Expo encerrou com codigo $LASTEXITCODE."
            }
        }

        & npx.cmd expo start --go --host lan --port $ExpoPort
        if ($LASTEXITCODE -ne 0) {
            throw "O Expo encerrou com codigo $LASTEXITCODE."
        }
    }
    finally {
        Pop-Location
    }
}
finally {
    if (-not $backendProcess.HasExited) {
        Stop-Process -Id $backendProcess.Id
        Write-Host 'Backend encerrado.'
    }
}
