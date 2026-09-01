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
exit 0
