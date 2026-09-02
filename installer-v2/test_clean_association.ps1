$ErrorActionPreference = "Stop"

$installer = (Resolve-Path "dist/CSM Visualizador XML 3.8.0 - Instalador Completo.exe").Path
$testDir = Join-Path $env:TEMP "CSMVisualizadorXML-Limpo-Homologacao"
$legacy1 = Join-Path $env:LOCALAPPDATA "CSMVisualizadorXML"
$legacy2 = Join-Path $env:LOCALAPPDATA "CSM Visualizador XML 4"

function Stop-CSMProcesses {
    Get-CimInstance Win32_Process |
        Where-Object { $_.Name -in @('CSM Visualizador XML.exe','CSM Visualizador XML Core.exe','CSMVisualizadorXML.exe') } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
}

Stop-CSMProcesses
Remove-Item $testDir -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item $legacy1 -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item $legacy2 -Recurse -Force -ErrorAction SilentlyContinue

# Cria resíduos equivalentes a instalações antigas.
New-Item -ItemType Directory -Force -Path $legacy1 | Out-Null
New-Item -ItemType Directory -Force -Path $legacy2 | Out-Null
"antigo" | Set-Content (Join-Path $legacy1 "residuo-antigo.txt")
"alpha" | Set-Content (Join-Path $legacy2 "residuo-alpha.txt")
New-Item -Path "Registry::HKEY_CURRENT_USER\Software\Classes\Applications\CSMVisualizadorXML.exe\shell\open\command" -Force | Out-Null
Set-ItemProperty -Path "Registry::HKEY_CURRENT_USER\Software\Classes\Applications\CSMVisualizadorXML.exe\shell\open\command" -Name '(default)' -Value 'C:\CAMINHO-ANTIGO\CSMVisualizadorXML.exe "%1"'
New-Item -Path "Registry::HKEY_CURRENT_USER\Software\Classes\CSMVisualizadorXML.xml" -Force | Out-Null
New-ItemProperty -Path "Registry::HKEY_CURRENT_USER\Software\RegisteredApplications" -Name "CSMVisualizadorXML" -Value "Software\Antigo\Capabilities" -PropertyType String -Force | Out-Null

$args = '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP- /DIR="' + $testDir + '"'
$p = Start-Process -FilePath $installer -ArgumentList $args -Wait -PassThru
if ($p.ExitCode -ne 0) { throw "Instalação silenciosa falhou: $($p.ExitCode)" }

$main = Join-Path $testDir "CSM Visualizador XML.exe"
$uninstaller = Join-Path $testDir "unins000.exe"
$buildInfo = Join-Path $testDir "_internal\csm\build-info.json"
if (!(Test-Path $main)) { throw "Executável atual não foi instalado" }
if (!(Test-Path $uninstaller)) { throw "Desinstalador atual não foi instalado" }
if (!(Test-Path $buildInfo)) { throw "Identidade 3.8.0 não foi instalada" }
$bi = Get-Content $buildInfo -Raw | ConvertFrom-Json
if ($bi.version -ne '3.8.0') { throw "Limpeza terminou com versão incorreta: $($bi.version)" }
if (Test-Path $legacy1) { throw "Pasta residual antiga permaneceu: $legacy1" }
if (Test-Path $legacy2) { throw "Pasta Alpha antiga permaneceu: $legacy2" }
if (Test-Path "Registry::HKEY_CURRENT_USER\Software\Classes\Applications\CSMVisualizadorXML.exe") { throw "Registro do executável antigo permaneceu" }
if (Test-Path "Registry::HKEY_CURRENT_USER\Software\Classes\CSMVisualizadorXML.xml") { throw "ProgID antigo permaneceu" }

$appCmdKey = "Registry::HKEY_CURRENT_USER\Software\Classes\Applications\CSM Visualizador XML.exe\shell\open\command"
$progCmdKey = "Registry::HKEY_CURRENT_USER\Software\Classes\CSM.VisualizadorXML.xml\shell\open\command"
$capKey = "Registry::HKEY_CURRENT_USER\Software\CSM\CSM Visualizador XML\Capabilities\FileAssociations"
$registeredKey = "Registry::HKEY_CURRENT_USER\Software\RegisteredApplications"

if (!(Test-Path $appCmdKey)) { throw "Comando atual de Abrir com não foi registrado" }
if (!(Test-Path $progCmdKey)) { throw "ProgID atual não foi registrado" }
if (!(Test-Path $capKey)) { throw "Capabilities de associação não foram registradas" }

$appCmd = (Get-ItemProperty -Path $appCmdKey).'(default)'
$progCmd = (Get-ItemProperty -Path $progCmdKey).'(default)'
$assoc = (Get-ItemProperty -Path $capKey).'.xml'
$registered = (Get-ItemProperty -Path $registeredKey).'CSM Visualizador XML'

$expectedExe = [Regex]::Escape($main)
if ($appCmd -notmatch $expectedExe) { throw "Abrir com aponta para caminho incorreto: $appCmd" }
if ($progCmd -notmatch $expectedExe) { throw "ProgID aponta para caminho incorreto: $progCmd" }
if ($assoc -ne 'CSM.VisualizadorXML.xml') { throw "Associação .xml incorreta: $assoc" }
if ($registered -ne 'Software\CSM\CSM Visualizador XML\Capabilities') { throw "RegisteredApplications incorreto: $registered" }

Write-Host "Limpeza total, versão 3.8.0 e novo registro XML validados."

Stop-CSMProcesses
$u = Start-Process -FilePath $uninstaller -ArgumentList '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART' -Wait -PassThru
if ($u.ExitCode -ne 0) { throw "Desinstalação de homologação falhou: $($u.ExitCode)" }
Start-Sleep -Milliseconds 800
if (Test-Path $main) { throw "Executável permaneceu após desinstalação" }
