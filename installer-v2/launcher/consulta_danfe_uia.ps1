param(
  [Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z0-9]{44}$')][string]$Key
)

$ErrorActionPreference = 'SilentlyContinue'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -AssemblyName System.Windows.Forms
Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class CSMInput {
  [DllImport("user32.dll")] public static extern bool SetCursorPos(int X, int Y);
  [DllImport("user32.dll")] public static extern void mouse_event(uint flags, uint dx, uint dy, uint data, UIntPtr extra);
}
"@

# CSM_LOOKUP_DOWNLOAD_V2
$logDir = Join-Path $env:LOCALAPPDATA 'CSM Visualizador XML\logs'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$log = Join-Path $logDir 'consulta-danfe-automacao.log'
function Log([string]$m) { Add-Content -Encoding UTF8 -Path $log -Value ((Get-Date -Format 'yyyy-MM-dd HH:mm:ss.fff') + ' ' + $m) }
function ClickPoint([int]$x,[int]$y) {
  [CSMInput]::SetCursorPos($x,$y) | Out-Null
  Start-Sleep -Milliseconds 80
  [CSMInput]::mouse_event(0x0002,0,0,0,[UIntPtr]::Zero)
  [CSMInput]::mouse_event(0x0004,0,0,0,[UIntPtr]::Zero)
}
function FindLookupWindow {
  $root=[System.Windows.Automation.AutomationElement]::RootElement
  $cond=New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty,[System.Windows.Automation.ControlType]::Window)
  $wins=$root.FindAll([System.Windows.Automation.TreeScope]::Children,$cond)
  foreach($w in $wins){
    $n=[string]$w.Current.Name
    if($n -match 'Consulta autom.tica|Consulta DANFE|CSM.*Consulta.*XML'){ return $w }
  }
  return $null
}
function TrySetKey($win) {
  $cond=New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty,[System.Windows.Automation.ControlType]::Edit)
  $edits=$win.FindAll([System.Windows.Automation.TreeScope]::Descendants,$cond)
  $candidates=@()
  foreach($e in $edits){
    $text=(([string]$e.Current.Name)+' '+([string]$e.Current.HelpText)+' '+([string]$e.Current.AutomationId)).ToLowerInvariant()
    $score=0
    if($text -match 'chave'){ $score+=10 }
    if($text -match '44'){ $score+=8 }
    if($text -match 'acesso'){ $score+=4 }
    $candidates += [pscustomobject]@{ E=$e; Score=$score }
  }
  foreach($c in ($candidates | Sort-Object Score -Descending)){
    try{
      $vp=[System.Windows.Automation.ValuePattern]$c.E.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern)
      $vp.SetValue($Key)
      Start-Sleep -Milliseconds 150
      if(([string]$vp.Current.Value).Replace(' ','').Replace('-','') -eq $Key){ Log 'Chave preenchida via UI Automation ValuePattern.'; return $true }
    }catch{}
    try{
      $c.E.SetFocus(); Start-Sleep -Milliseconds 100
      [System.Windows.Forms.SendKeys]::SendWait('^a')
      [System.Windows.Forms.SendKeys]::SendWait($Key)
      Log 'Chave enviada via foco/SendKeys.'
      return $true
    }catch{}
  }
  return $false
}
function TryInvokeSearch($win) {
  $cond=New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty,[System.Windows.Automation.ControlType]::Button)
  $buttons=$win.FindAll([System.Windows.Automation.TreeScope]::Descendants,$cond)
  foreach($b in $buttons){
    $n=[string]$b.Current.Name
    if($n -match 'Imprimir DANFE|Buscar|Consultar'){
      try{
        $ip=[System.Windows.Automation.InvokePattern]$b.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern)
        $ip.Invoke(); Log ('Consulta acionada via botão UIA: '+$n); return $true
      }catch{}
    }
  }
  return $false
}
function TryInvokeElement($element,[string]$label) {
  try {
    $ip=[System.Windows.Automation.InvokePattern]$element.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern)
    $ip.Invoke(); Log ('Download acionado via InvokePattern: '+$label); return $true
  } catch {}
  try {
    $sp=[System.Windows.Automation.SelectionItemPattern]$element.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern)
    $sp.Select(); Log ('Download acionado via SelectionItemPattern: '+$label); return $true
  } catch {}
  try {
    $element.SetFocus(); Start-Sleep -Milliseconds 80
    [System.Windows.Forms.SendKeys]::SendWait('{ENTER}')
    Log ('Download acionado por foco/ENTER: '+$label); return $true
  } catch {}
  try {
    $r=$element.Current.BoundingRectangle
    if($r.Width -gt 4 -and $r.Height -gt 4){
      ClickPoint ([int]($r.Left+$r.Width/2)) ([int]($r.Top+$r.Height/2))
      Log ('Download acionado por clique no centro do controle: '+$label); return $true
    }
  } catch {}
  return $false
}
function TryInvokeDownloadXml($win) {
  $types=@(
    [System.Windows.Automation.ControlType]::Button,
    [System.Windows.Automation.ControlType]::Hyperlink,
    [System.Windows.Automation.ControlType]::Text,
    [System.Windows.Automation.ControlType]::Custom
  )
  $all=$win.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
  $candidates=@()
  foreach($e in $all){
    try {
      $ct=$e.Current.ControlType
      if($types -notcontains $ct){ continue }
      $n=[string]$e.Current.Name
      $help=[string]$e.Current.HelpText
      $aid=[string]$e.Current.AutomationId
      $text=($n+' '+$help+' '+$aid).Trim()
      $low=$text.ToLowerInvariant()
      $score=0
      if($low -match 'baixar\s+xml'){ $score+=30 }
      if($low -match 'download\s+xml'){ $score+=25 }
      if($low -match '\bxml\b'){ $score+=8 }
      if($low -match 'baixar|download'){ $score+=8 }
      if($low -match 'danfe|pdf'){ $score-=10 }
      if($score -ge 16){ $candidates += [pscustomobject]@{ E=$e; Score=$score; Label=$text } }
    } catch {}
  }
  foreach($c in ($candidates | Sort-Object Score -Descending)){
    if(TryInvokeElement $c.E $c.Label){ return $true }
  }
  return $false
}

Log ('Iniciando automação reforçada para chave '+$Key.Substring(0,4)+'...'+$Key.Substring(40,4))
$deadline=(Get-Date).AddSeconds(32)
$win=$null
while((Get-Date) -lt $deadline){
  $win=FindLookupWindow
  if($win){ break }
  Start-Sleep -Milliseconds 250
}
if(-not $win){ Log 'Janela de consulta não encontrada no prazo.'; exit 2 }
Start-Sleep -Milliseconds 700

$filled=$false
for($i=0;$i -lt 20 -and -not $filled;$i++){
  $filled=TrySetKey $win
  if(-not $filled){ Start-Sleep -Milliseconds 300 }
}

if(-not $filled){
  # Fallback visual somente se a árvore de acessibilidade do WebView2 não expuser o input.
  # As coordenadas são relativas à janela, não ao monitor, para tolerar resoluções diferentes.
  $r=$win.Current.BoundingRectangle
  $x=[int]($r.Left + ($r.Width * 0.40)); $y=[int]($r.Top + ($r.Height * 0.645))
  ClickPoint $x $y
  [System.Windows.Forms.SendKeys]::SendWait('^a')
  [System.Windows.Forms.SendKeys]::SendWait($Key)
  $filled=$true
  Log 'Chave preenchida pelo fallback visual relativo.'
}

Start-Sleep -Milliseconds 250
if(-not (TryInvokeSearch $win)){
  try{ [System.Windows.Forms.SendKeys]::SendWait('{ENTER}'); Log 'Consulta acionada por ENTER.' }catch{}
}

# Após a consulta, aguarda a página de resultado liberar o botão/link de XML.
# Se houver CAPTCHA, o usuário pode resolvê-lo manualmente; a automação continua aguardando.
Log 'Aguardando controle Baixar XML após a consulta.'
$downloadDeadline=(Get-Date).AddSeconds(120)
$downloadClicked=$false
while((Get-Date) -lt $downloadDeadline -and -not $downloadClicked){
  $win=FindLookupWindow
  if(-not $win){ Log 'Janela de consulta fechada antes do clique em Baixar XML.'; exit 3 }
  $downloadClicked=TryInvokeDownloadXml $win
  if(-not $downloadClicked){ Start-Sleep -Milliseconds 350 }
}
if($downloadClicked){ Log 'Baixar XML acionado automaticamente com sucesso.'; exit 0 }
Log 'Botão/link Baixar XML não ficou disponível no prazo.'
exit 4
