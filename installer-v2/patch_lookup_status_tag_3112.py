from pathlib import Path

MARKER='CSM_LOOKUP_STATUS_TAG_3112'
p=Path('installer-v2/launcher/consulta_danfe_helper.cs')
s=p.read_text(encoding='utf-8')
if MARKER in s:
    print('Status da consulta 3.11.2 já aplicado')
    raise SystemExit(0)

s=s.replace('var target = Path.Combine(downloads, key + ".xml");','var target = Path.Combine(downloads, key + "-" + DateTime.Now.ToString("HHmmssfff") + ".xml");',1)
old='''                    var status = DetectDocumentStatus(win);\n                    Log("XML válido localizado: " + matching + " | situação=" + status);\n                    NotifyBrokerOpen(matching);'''
new='''                    var status = DetectDocumentStatus(win);\n                    matching = TagXmlWithStatus(matching, key, status);\n                    Log("XML válido localizado: " + matching + " | situação=" + status);\n                    NotifyBrokerOpen(matching);'''
if old not in s:
    raise RuntimeError('Bloco de status esperado não encontrado')
s=s.replace(old,new,1)

anchor='''    private static void NotifyBrokerOpen(string path)\n    {'''
helper='''    // CSM_LOOKUP_STATUS_TAG_3112\n    private static string TagXmlWithStatus(string path, string key, string status)\n    {\n        try\n        {\n            if (String.IsNullOrWhiteSpace(path) || !File.Exists(path)) return path;\n            var safe = status == "CANCELADA" || status == "DENEGADA" || status == "AUTORIZADA" ? status : "ENCONTRADA";\n            var dir = Path.GetDirectoryName(path) ?? "";\n            var target = Path.Combine(dir, key + " - " + safe + " - " + DateTime.Now.ToString("HHmmssfff") + ".xml");\n            if (!String.Equals(path, target, StringComparison.OrdinalIgnoreCase))\n            {\n                File.Move(path, target);\n                return target;\n            }\n        }\n        catch (Exception ex) { Log("Não foi possível marcar situação no nome do XML: " + ex.Message); }\n        return path;\n    }\n\n'''
if anchor not in s:
    raise RuntimeError('Âncora NotifyBrokerOpen não encontrada')
s=s.replace(anchor,helper+anchor,1)
p.write_text(s,encoding='utf-8',newline='\n')
print('Helper 3.11.2: status AUTORIZADA/CANCELADA/DENEGADA acompanha o XML aberto.')
