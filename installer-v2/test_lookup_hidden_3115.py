from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else 'installer-v2/launcher/consulta_danfe_helper.cs')
s=p.read_text(encoding='utf-8')
for tok in (
    'CSM_LOOKUP_HIDDEN_WINDOW_3115','ShowWindow','SW_HIDE','_managedLookupWindow',
    'HideLookupWindow(win)','IsLookupWindowAlive(win)','CloseLookupWindow(_managedLookupWindow)',
    'RevealLookupWindow(win)','janela exibida somente para intervenção manual'
):
    if tok not in s: raise SystemExit('Helper 3.11.5 sem token: '+tok)
# A consulta precisa esconder depois de acionar a busca e fechar via finally.
main=s[s.find('private static int Main'):s.find('private static string NormalizeKey')]
if main.find('TryInvokeSearch(win)')<0 or main.find('HideLookupWindow(win)')<main.find('TryInvokeSearch(win)'):
    raise SystemExit('Janela foi ocultada antes da consulta ser acionada')
if 'finally' not in main or 'CloseLookupWindow(_managedLookupWindow)' not in main:
    raise SystemExit('Janela externa não é encerrada no final')
if 'win = FindLookupWindow();' in main:
    raise SystemExit('Loop ainda tenta reencontrar a janela depois de ocultá-la')
print('OK - helper 3.11.5 mantém referência da janela, oculta o provedor, revela só em desafio manual e fecha ao terminar.')
