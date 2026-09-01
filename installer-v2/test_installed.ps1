$ErrorActionPreference = "Stop"

$installer = (Resolve-Path "dist/CSMVisualizadorXML-Instalador-Completo-Abas-Fix.exe").Path
$testDir = Join-Path $env:TEMP "CSMVisualizadorXML-AbasFix-Homologacao"
$legacy = Join-Path $env:LOCALAPPDATA "CSMVisualizadorXML"
$desktop = [Environment]::GetFolderPath('Desktop')
$shortcut = Join-Path $desktop "CSM Visualizador XML.lnk"

function Stop-CSMProcesses {
    Get-CimInstance Win32_Process |
        Where-Object { $_.Name -in @('CSM Visualizador XML.exe','CSM Visualizador XML Core.exe') } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
}

function Get-CoreIds {
    return @(Get-CimInstance Win32_Process |
        Where-Object { $_.Name -eq 'CSM Visualizador XML Core.exe' } |
        Select-Object -ExpandProperty ProcessId |
        Sort-Object)
}

Remove-Item $testDir -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item $legacy -Recurse -Force -ErrorAction SilentlyContinue
Stop-CSMProcesses
New-Item -ItemType Directory -Force -Path $legacy | Out-Null
"residuo-antigo" | Set-Content (Join-Path $legacy "residuo.txt")

$args = '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP- /DIR="' + $testDir + '"'
$p = Start-Process -FilePath $installer -ArgumentList $args -Wait -PassThru
if ($p.ExitCode -ne 0) { throw "Instalação silenciosa falhou: $($p.ExitCode)" }

$main = Join-Path $testDir "CSM Visualizador XML.exe"
$core = Join-Path $testDir "CSM Visualizador XML Core.exe"
$uninstaller = Join-Path $testDir "unins000.exe"
$appjs = Join-Path $testDir "_internal\web\app.js"
$refcss = Join-Path $testDir "_internal\web\refinement.css"

if (!(Test-Path $main)) { throw "Launcher principal não instalado" }
if (!(Test-Path $core)) { throw "Core do Visualizador não instalado" }
if (!(Test-Path $uninstaller)) { throw "Desinstalador não instalado" }
if (Test-Path (Join-Path $legacy "residuo.txt")) { throw "Resíduo de versão antiga não foi removido" }
if (!(Test-Path $shortcut)) { throw "Atalho da Área de Trabalho não foi criado" }
if (!(Test-Path "Registry::HKEY_CURRENT_USER\Software\Classes\Applications\CSM Visualizador XML.exe\shell\open\command")) { throw "Registro Abrir com não foi criado" }
if (!(Select-String -Path $appjs -Pattern "companyTabLabel" -Quiet)) { throw "Etiqueta de empresa não instalada" }
if (!(Select-String -Path $appjs -Pattern "MATRIZ.*FILIAL|FILIAL.*MATRIZ" -Quiet)) { throw "Identificação MATRIZ/FILIAL não instalada" }
if (!(Select-String -Path $appjs -Pattern "setupExternalOpenBridge" -Quiet)) { throw "Bridge externo não instalado" }
if (!(Select-String -Path $appjs -Pattern "acknowledgeExternalDocument" -Quiet)) { throw "Confirmação da abertura externa não instalada" }
if (!(Select-String -Path $refcss -Pattern "body.light .meta-row .value" -Quiet)) { throw "Correção do tema claro não instalada" }

$launchTest = Start-Process -FilePath $main -ArgumentList '--csm-launcher-selftest' -Wait -PassThru
if ($launchTest.ExitCode -ne 0) { throw "Launcher instalado falhou no self-test" }

$sample = Join-Path $env:TEMP "CSM Visualizador XML teste.xml"
$sampleXml = '<?xml version="1.0" encoding="UTF-8"?><NFe xmlns="http://www.portalfiscal.inf.br/nfe"><infNFe Id="NFe35260811129502000486550010000342541000000006" versao="4.00"><ide><cUF>35</cUF><cNF>00000000</cNF><natOp>VENDA</natOp><mod>55</mod><serie>16</serie><nNF>34254</nNF><dhEmi>2026-08-16T00:00:00-03:00</dhEmi><tpNF>1</tpNF><idDest>1</idDest><cMunFG>3550308</cMunFG><tpImp>1</tpImp><tpEmis>1</tpEmis><cDV>6</cDV><tpAmb>1</tpAmb><finNFe>1</finNFe><indFinal>1</indFinal><indPres>1</indPres><procEmi>0</procEmi><verProc>CSM</verProc></ide><emit><CNPJ>11129502000486</CNPJ><xNome>PIRUETA COMERCIAL LTDA</xNome><enderEmit><xLgr>RUA TESTE</xLgr><nro>1</nro><xBairro>CENTRO</xBairro><cMun>3550308</cMun><xMun>SAO PAULO</xMun><UF>SP</UF><CEP>01001000</CEP><cPais>1058</cPais><xPais>BRASIL</xPais></enderEmit><IE>118548090114</IE><CRT>3</CRT></emit><dest><CPF>00000000191</CPF><xNome>CONSUMIDOR NAO IDENTIFICADO</xNome><indIEDest>9</indIEDest></dest><det nItem="1"><prod><cProd>1</cProd><cEAN>SEM GTIN</cEAN><xProd>PRODUTO TESTE</xProd><NCM>00000000</NCM><CFOP>5102</CFOP><uCom>UN</uCom><qCom>1.0000</qCom><vUnCom>23.8900000000</vUnCom><vProd>23.89</vProd><cEANTrib>SEM GTIN</cEANTrib><uTrib>UN</uTrib><qTrib>1.0000</qTrib><vUnTrib>23.8900000000</vUnTrib><indTot>1</indTot></prod><imposto><ICMS><ICMS00><orig>0</orig><CST>00</CST><modBC>3</modBC><vBC>23.89</vBC><pICMS>18.0000</pICMS><vICMS>4.30</vICMS></ICMS00></ICMS><PIS><PISAliq><CST>01</CST><vBC>23.89</vBC><pPIS>1.6500</pPIS><vPIS>0.39</vPIS></PISAliq></PIS><COFINS><COFINSAliq><CST>01</CST><vBC>23.89</vBC><pCOFINS>7.6000</pCOFINS><vCOFINS>1.82</vCOFINS></COFINSAliq></COFINS></imposto></det><total><ICMSTot><vBC>23.89</vBC><vICMS>4.30</vICMS><vICMSDeson>0.00</vICMSDeson><vFCP>0.00</vFCP><vBCST>0.00</vBCST><vST>0.00</vST><vFCPST>0.00</vFCPST><vFCPSTRet>0.00</vFCPSTRet><vProd>23.89</vProd><vFrete>0.00</vFrete><vSeg>0.00</vSeg><vDesc>0.00</vDesc><vII>0.00</vII><vIPI>0.00</vIPI><vIPIDevol>0.00</vIPIDevol><vPIS>0.39</vPIS><vCOFINS>1.82</vCOFINS><vOutro>0.00</vOutro><vNF>23.89</vNF></ICMSTot></total><transp><modFrete>9</modFrete></transp><pag><detPag><tPag>01</tPag><vPag>23.89</vPag></detPag></pag></infNFe></NFe>'
Set-Content -Path $sample -Value $sampleXml -Encoding utf8

$primary = Start-Process -FilePath $main -PassThru

$health = $null
for($i=0;$i -lt 100;$i++) {
    try {
        $health = Invoke-RestMethod -Uri 'http://127.0.0.1:47878/health' -TimeoutSec 1
        if($health.ok -and [int]$health.subscribers -ge 1) { break }
    } catch {}
    Start-Sleep -Milliseconds 250
}
if(!$health -or !$health.ok) { throw "Broker de instância única não iniciou" }
if([int]$health.subscribers -lt 1) { throw "Interface não conectou ao broker de abas" }

# Aguarda o conjunto de processos internos estabilizar. PyInstaller pode usar pai + filho para uma única janela.
$previous = ''
$stableReadings = 0
$before = @()
for($i=0;$i -lt 30;$i++) {
    $before = @(Get-CoreIds)
    $current = ($before -join ',')
    if($current -and $current -eq $previous) { $stableReadings++ } else { $stableReadings = 0 }
    if($stableReadings -ge 2) { break }
    $previous = $current
    Start-Sleep -Milliseconds 350
}
if($before.Count -lt 1) { throw "Nenhum processo Core encontrado após inicialização" }
$beforeIds = ($before -join ',')
Write-Host "Core antes da segunda nota: $beforeIds"

$second = Start-Process -FilePath $main -ArgumentList ('"' + $sample + '"') -Wait -PassThru
if($second.ExitCode -ne 0) { throw "Segunda abertura pelo Windows falhou" }

$health2 = $null
for($i=0;$i -lt 60;$i++) {
    try {
        $health2 = Invoke-RestMethod -Uri 'http://127.0.0.1:47878/health' -TimeoutSec 1
        if($health2.ok -and [int]$health2.ack_count -ge 1) { break }
    } catch {}
    Start-Sleep -Milliseconds 250
}
if(!$health2 -or !$health2.ok) { throw "Broker deixou de responder após segunda nota" }
if([int]$health2.subscribers -lt 1) { throw "Bridge de abas desconectou após segunda nota" }
if([int]$health2.ack_count -lt 1) { throw "A interface não confirmou o processamento do XML externo" }

$after = @(Get-CoreIds)
$afterIds = ($after -join ',')
if($afterIds -ne $beforeIds) { throw "A segunda nota relançou o Core. Antes=$beforeIds Depois=$afterIds" }
Write-Host "Instância lógica única OK. Core(s): $afterIds. ACK=$($health2.ack_count)."

$htmls = Get-ChildItem $testDir -Recurse -File -Include *.html,*.htm
$marker = $false
foreach ($h in $htmls) {
    if (Select-String -Path $h.FullName -Pattern "CSM_XML_ENHANCER_V8" -Quiet -ErrorAction SilentlyContinue) { $marker = $true; break }
}
if (!$marker) { throw "Aba XML v8 não encontrada nos arquivos instalados" }

$up = Start-Process -FilePath $uninstaller -ArgumentList '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART' -Wait -PassThru
if ($up.ExitCode -ne 0) { throw "Desinstalação silenciosa falhou: $($up.ExitCode)" }
Start-Sleep -Milliseconds 1000
if (Test-Path $main) { throw "Launcher permaneceu após desinstalação" }
if (Test-Path $core) { throw "Core permaneceu após desinstalação" }
if (Test-Path $shortcut) { throw "Atalho da Área de Trabalho permaneceu após desinstalação" }

Write-Host "Homologação completa concluída com sucesso."
