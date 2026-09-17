from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else 'installer-v2/launcher/consulta_danfe_helper.cs')
s=p.read_text(encoding='utf-8')
for tok in (
    'CSM_LOOKUP_HIDDEN_WINDOW_3115','ShowWindow','SW_HIDE','_managedLookupWindow','Thread.Sleep(35)',
    'HideLookupWindow(win)','IsLookupWindowAlive(win)','CloseLookupWindow(_managedLookupWindow)',
    'RevealLookupWindow(win)','janela exibida somente para intervenção manual'
):
    if tok not in s: raise SystemExit('Helper 3.11.5 sem token: '+tok)
main=s[s.find('private static int Main'):s.find('private static string NormalizeKey')]
wait_pos=main.find('WaitForLookupWindow')
hide_pos=main.find('HideLookupWindow(win)')
key_pos=main.find('TrySetKey(win, key)')
search_pos=main.find('TryInvokeSearch(win)')
if min(wait_pos,hide_pos,key_pos,search_pos)<0:
    raise SystemExit('Fluxo principal da consulta ocultada incompleto')
if not (wait_pos < hide_pos < key_pos < search_pos):
    raise SystemExit('Provedor não é ocultado imediatamente antes de preencher/consultar')
if 'finally' not in main or 'CloseLookupWindow(_managedLookupWindow)' not in main:
    raise SystemExit('Janela externa não é encerrada no final')
if 'win = FindLookupWindow();' in main:
    raise SystemExit('Loop ainda tenta reencontrar a janela depois de ocultá-la')
print('OK - provedor é capturado em baixa latência, ocultado antes do preenchimento, revelado só em fallback/desafio e fechado ao terminar.')
