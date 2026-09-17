from pathlib import Path

MARKER='CSM_LOOKUP_NO_SPREADSHEET_3114'
p=Path('installer-v2/launcher/consulta_danfe_helper.cs')
s=p.read_text(encoding='utf-8')
if MARKER in s:
    print('Proteção anti-planilha 3.11.4 já aplicada')
    raise SystemExit(0)

# O vídeo real mostrou o Salvar Como com nome "Biblioteca de XMLs" e tipo
# "Planilha Excel (*.xlsx)". Na 3.11.2 a checagem olhava só o nome sugerido;
# por isso "Biblioteca de XMLs" escapava. Agora nome E tipo de arquivo são
# lidos diretamente do diálogo do Windows.
old='''    private static bool IsSpreadsheetText(string text)\n    {\n        text = NormalizeText(text);\n        return text.Contains("excel") || text.Contains("xlsx") || text.Contains("xls") || text.Contains("csv") || text.Contains("planilha") || text.Contains("exportar");\n    }'''
new='''    // CSM_LOOKUP_NO_SPREADSHEET_3114\n    private static bool IsSpreadsheetText(string text)\n    {\n        text = NormalizeText(text);\n        return text.Contains("excel") || text.Contains("xlsx") || text.Contains(".xls") || text.Contains("csv") || text.Contains("planilha") || text.Contains("exportar") || text.Contains("biblioteca de xml");\n    }'''
if old not in s: raise RuntimeError('IsSpreadsheetText 3.11.2 não encontrado')
s=s.replace(old,new,1)

anchor='''    private static void CancelUnexpectedSpreadsheetSaveDialog()\n    {'''
helper='''    private static string GetSaveDialogFileType(AutomationElement dlg)\n    {\n        try\n        {\n            foreach (AutomationElement e in SafeDescendants(dlg))\n            {\n                var ct=e.Current.ControlType;\n                if (ct != ControlType.ComboBox && ct != ControlType.Text) continue;\n                var meta=ElementText(e);\n                if (meta.Contains("tipo") || meta.Contains("type") || meta.Contains("excel") || meta.Contains("xlsx") || meta.Contains("csv") || meta.Contains("planilha"))\n                {\n                    var value=""; object ptn;\n                    try { if (e.TryGetCurrentPattern(ValuePattern.Pattern,out ptn)) value=((ValuePattern)ptn).Current.Value??""; } catch { }\n                    return meta+" "+value;\n                }\n            }\n        }\n        catch { }\n        return "";\n    }\n\n'''
if anchor not in s: raise RuntimeError('CancelUnexpectedSpreadsheetSaveDialog não encontrado')
s=s.replace(anchor,helper+anchor,1)

old_cancel='''        var all = SafeDescendants(dlg);\n        var suggested = GetSaveDialogFileName(dlg);\n        if (!IsSpreadsheetText(suggested)) return;'''
new_cancel='''        var all = SafeDescendants(dlg);\n        var suggested = GetSaveDialogFileName(dlg);\n        var fileType = GetSaveDialogFileType(dlg);\n        if (!IsSpreadsheetText(suggested + " " + fileType)) return;\n        Log("Bloqueando Salvar Como de planilha: nome=" + suggested + " | tipo=" + fileType);'''
if old_cancel not in s: raise RuntimeError('Checagem de planilha no cancel não encontrada')
s=s.replace(old_cancel,new_cancel,1)

old_confirm='''        var all = SafeDescendants(dlg);\n        var suggested = GetSaveDialogFileName(dlg);\n        if (IsSpreadsheetText(suggested)) { CancelUnexpectedSpreadsheetSaveDialog(); return false; }'''
new_confirm='''        var all = SafeDescendants(dlg);\n        var suggested = GetSaveDialogFileName(dlg);\n        var fileType = GetSaveDialogFileType(dlg);\n        if (IsSpreadsheetText(suggested + " " + fileType)) { CancelUnexpectedSpreadsheetSaveDialog(); return false; }'''
if old_confirm not in s: raise RuntimeError('Checagem de planilha no confirm XML não encontrada')
s=s.replace(old_confirm,new_confirm,1)

# Defesa adicional: nunca trate Biblioteca de XMLs / exportação como ação de XML.
old_filter='''            if (IsSpreadsheetText(text) || text.Contains("pdf") || text.Contains("danfe")) continue;'''
new_filter='''            if (IsSpreadsheetText(text) || text.Contains("biblioteca") || text.Contains("exportar") || text.Contains("pdf") || text.Contains("danfe")) continue;'''
if old_filter not in s: raise RuntimeError('Filtro do download XML estrito não encontrado')
s=s.replace(old_filter,new_filter,1)

for tok in (MARKER,'GetSaveDialogFileType','biblioteca de xml','Bloqueando Salvar Como de planilha'):
    if tok not in s: raise SystemExit('Proteção 3.11.4 incompleta: '+tok)
p.write_text(s,encoding='utf-8',newline='\n')
print('3.11.4: Biblioteca de XMLs / Excel / XLSX / CSV são cancelados pelo nome e pelo tipo do Salvar Como.')
