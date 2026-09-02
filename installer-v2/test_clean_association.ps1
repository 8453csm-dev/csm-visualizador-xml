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
$appJs = Join-Path $testDir "_internal\web\app.js"
$iconFile = Join-Path $testDir "_internal\assets\CSMVisualizadorXML.ico"
if (!(Test-Path $main)) { throw "Executável atual não foi instalado" }
if (!(Test-Path $uninstaller)) { throw "Desinstalador atual não foi instalado" }
if (!(Test-Path $buildInfo)) { throw "Identidade 3.8.0 não foi instalada" }
if (!(Test-Path $appJs)) { throw "Frontend instalado não foi encontrado" }
if (!(Test-Path $iconFile)) { throw "Ícone profissional do CSM não foi instalado" }
$bi = Get-Content $buildInfo -Raw -Encoding UTF8 | ConvertFrom-Json
if ($bi.version -ne '3.8.0') { throw "Limpeza terminou com versão incorreta: $($bi.version)" }

# Lê como UTF-8 explicitamente. Select-String no runner já gerou falso negativo
# com o literal acentuado do modal Sobre, apesar do patch ter sido aplicado.
$appText = Get-Content $appJs -Raw -Encoding UTF8
$aboutToken = "els.aboutVersion.textContent='Versão 3.8.0'"
$aboutCount = ([regex]::Matches($appText, [regex]::Escape($aboutToken))).Count
Write-Host "Ocorrências da versão visual 3.8.0 no app instalado: $aboutCount"
if ($aboutCount -lt 2) {
    Write-Host "Linhas aboutVersion encontradas no app instalado:"
    (($appText -split "`n") | Where-Object { $_ -match 'aboutVersion' }) | ForEach-Object { Write-Host $_ }
    throw "A versão visual do modal Sobre ainda não está fixada em 3.8.0 (ocorrências: $aboutCount)"
}
if ($appText.Contains('aboutVersion.textContent=`Versão ${r?.version')) {
    throw "Modal Sobre ainda depende do get_app_info() antigo"
}
if ($appText.Contains('aboutVersion.textContent=`Versão ${r.current')) {
    throw "Verificação de atualização ainda pode restaurar versão antiga no Sobre"
}

if (Test-Path $legacy1) { throw "Pasta residual antiga permaneceu: $legacy1" }
if (Test-Path $legacy2) { throw "Pasta Alpha antiga permaneceu: $legacy2" }
if (Test-Path "Registry::HKEY_CURRENT_USER\Software\Classes\Applications\CSMVisualizadorXML.exe") { throw "Registro do executável antigo permaneceu" }
if (Test-Path "Registry::HKEY_CURRENT_USER\Software\Classes\CSMVisualizadorXML.xml") { throw "ProgID antigo permaneceu" }

$appCmdKey = "Registry::HKEY_CURRENT_USER\Software\Classes\Applications\CSM Visualizador XML.exe\shell\open\command"
$appIconKey = "Registry::HKEY_CURRENT_USER\Software\Classes\Applications\CSM Visualizador XML.exe\DefaultIcon"
$progCmdKey = "Registry::HKEY_CURRENT_USER\Software\Classes\CSM.VisualizadorXML.xml\shell\open\command"
$progIconKey = "Registry::HKEY_CURRENT_USER\Software\Classes\CSM.VisualizadorXML.xml\DefaultIcon"
$capRoot = "Registry::HKEY_CURRENT_USER\Software\CSM\CSM Visualizador XML\Capabilities"
$capKey = "$capRoot\FileAssociations"
$registeredKey = "Registry::HKEY_CURRENT_USER\Software\RegisteredApplications"
$appPathKey = "Registry::HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\App Paths\CSM Visualizador XML.exe"

foreach ($key in @($appCmdKey,$appIconKey,$progCmdKey,$progIconKey,$capRoot,$capKey,$appPathKey)) {
    if (!(Test-Path $key)) { throw "Registro profissional ausente: $key" }
}

$appCmd = (Get-ItemProperty -Path $appCmdKey).'(default)'
$appIcon = (Get-ItemProperty -Path $appIconKey).'(default)'
$progCmd = (Get-ItemProperty -Path $progCmdKey).'(default)'
$progIcon = (Get-ItemProperty -Path $progIconKey).'(default)'
$capIcon = (Get-ItemProperty -Path $capRoot).'ApplicationIcon'
$assoc = (Get-ItemProperty -Path $capKey).'.xml'
$registered = (Get-ItemProperty -Path $registeredKey).'CSM Visualizador XML'
$appPath = (Get-ItemProperty -Path $appPathKey).'(default)'

$expectedExe = [Regex]::Escape($main)
$expectedIcon = [Regex]::Escape($iconFile)
if ($appCmd -notmatch $expectedExe) { throw "Abrir com aponta para caminho incorreto: $appCmd" }
if ($progCmd -notmatch $expectedExe) { throw "ProgID aponta para caminho incorreto: $progCmd" }
if ($appPath -notmatch $expectedExe) { throw "App Paths aponta para caminho incorreto: $appPath" }
if ($appIcon -notmatch $expectedIcon) { throw "Applications DefaultIcon incorreto: $appIcon" }
if ($progIcon -notmatch $expectedIcon) { throw "ProgID DefaultIcon incorreto: $progIcon" }
if ($capIcon -notmatch $expectedIcon) { throw "Capabilities ApplicationIcon incorreto: $capIcon" }
if ($assoc -ne 'CSM.VisualizadorXML.xml') { throw "Associação .xml incorreta: $assoc" }
if ($registered -ne 'Software\CSM\CSM Visualizador XML\Capabilities') { throw "RegisteredApplications incorreto: $registered" }

Write-Host "Limpeza total, modal Sobre 3.8.0 e identidade visual da associação XML validados."

Stop-CSMProcesses
$u = Start-Process -FilePath $uninstaller -ArgumentList '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART' -Wait -PassThru
if ($u.ExitCode -ne 0) { throw "Desinstalação de homologação falhou: $($u.ExitCode)" }
Start-Sleep -Milliseconds 800
if (Test-Path $main) { throw "Executável permaneceu após desinstalação" }
