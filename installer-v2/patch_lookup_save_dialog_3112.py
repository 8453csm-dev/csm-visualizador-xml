from pathlib import Path

MARKER='CSM_LOOKUP_SAVE_DIALOG_3112'
p=Path('installer-v2/launcher/consulta_danfe_helper.cs')
s=p.read_text(encoding='utf-8')
if MARKER in s:
    print('Save dialog 3.11.2 já refinado')
    raise SystemExit(0)

anchor='''    private static void CancelUnexpectedSpreadsheetSaveDialog()\n    {'''
helper='''    // CSM_LOOKUP_SAVE_DIALOG_3112\n    private static string GetSaveDialogFileName(AutomationElement dlg)\n    {\n        try\n        {\n            foreach (AutomationElement e in SafeDescendants(dlg))\n            {\n                if (e.Current.ControlType != ControlType.Edit) continue;\n                var meta = ElementText(e);\n                object p;\n                if (e.TryGetCurrentPattern(ValuePattern.Pattern, out p))\n                {\n                    var v = ((ValuePattern)p).Current.Value ?? "";\n                    if (meta.Contains("nome") || meta.Contains("arquivo") || meta.Contains("file name") || v.Contains(".")) return v;\n                }\n            }\n        }\n        catch { }\n        return "";\n    }\n\n'''
if anchor not in s: raise RuntimeError('Âncora CancelUnexpectedSpreadsheetSaveDialog não encontrada')
s=s.replace(anchor,helper+anchor,1)

old='''        var all = SafeDescendants(dlg);\n        var text = "";\n        foreach (AutomationElement e in all) text += " " + ElementText(e);\n        if (!IsSpreadsheetText(text)) return;'''
new='''        var all = SafeDescendants(dlg);\n        var suggested = GetSaveDialogFileName(dlg);\n        if (!IsSpreadsheetText(suggested)) return;'''
if old not in s: raise RuntimeError('Detecção ampla de planilha não encontrada')
s=s.replace(old,new,1)

old2='''        var all = SafeDescendants(dlg);\n        var joined = "";\n        foreach (AutomationElement e in all) joined += " " + ElementText(e);\n        if (IsSpreadsheetText(joined)) { CancelUnexpectedSpreadsheetSaveDialog(); return false; }'''
new2='''        var all = SafeDescendants(dlg);\n        var suggested = GetSaveDialogFileName(dlg);\n        if (IsSpreadsheetText(suggested)) { CancelUnexpectedSpreadsheetSaveDialog(); return false; }'''
if old2 not in s: raise RuntimeError('Detecção ampla no confirm XML não encontrada')
s=s.replace(old2,new2,1)
p.write_text(s,encoding='utf-8',newline='\n')
print('Save dialog 3.11.2: Excel/CSV detectado pelo nome sugerido, sem falso positivo por arquivos da pasta.')
