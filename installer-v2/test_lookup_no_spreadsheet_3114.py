from pathlib import Path
import sys

p=Path(sys.argv[1]) if len(sys.argv)>1 else Path('installer-v2/launcher/consulta_danfe_helper.cs')
s=p.read_text(encoding='utf-8')
required=(
 'CSM_LOOKUP_NO_SPREADSHEET_3114',
 'GetSaveDialogFileType',
 'biblioteca de xml',
 'Bloqueando Salvar Como de planilha',
 'TryInvokeDownloadXmlStrict',
 'ValidateXmlForKey',
 'NotifyBrokerOpen',
)
for tok in required:
    if tok not in s: raise SystemExit('Proteção ausente: '+tok)
# Não basta haver a palavra Excel: o bloqueio precisa considerar nome + tipo.
if 'suggested + " " + fileType' not in s:
    raise SystemExit('Salvar Como não combina nome e tipo de arquivo')
if 'text.Contains("biblioteca") || text.Contains("exportar")' not in s:
    raise SystemExit('Download XML ainda pode aceitar Biblioteca/exportação')
print('OK - Biblioteca de XMLs, Excel/XLSX/CSV são bloqueados e somente XML validado pela chave pode abrir no CSM.')
