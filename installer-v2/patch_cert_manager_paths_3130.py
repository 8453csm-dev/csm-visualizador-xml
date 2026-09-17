from pathlib import Path

p=Path('installer-v2/launcher/csm_fiscal_core.cs')
s=p.read_text(encoding='utf-8')
MARK='CSM_CERT_MANAGER_PATHS_3130'
if MARK in s:
    print('Normalização de caminhos 3.13.0 já aplicada')
    raise SystemExit(0)

old='''                    string value = Convert.ToString(x, CultureInfo.InvariantCulture) ?? "";\n                    if (!String.IsNullOrWhiteSpace(value) && !folders.Any(v => String.Equals(v, value, StringComparison.OrdinalIgnoreCase))) folders.Add(value);'''
new='''                    string value = NormalizeConfiguredPath(Convert.ToString(x, CultureInfo.InvariantCulture) ?? "");\n                    if (!String.IsNullOrWhiteSpace(value) && !folders.Any(v => String.Equals(v, value, StringComparison.OrdinalIgnoreCase))) folders.Add(value);'''
if old not in s: raise SystemExit('Leitura de folders não localizada')
s=s.replace(old,new,1)

old='''            try { path = Path.GetFullPath(path); } catch { }'''
new='''            path = NormalizeConfiguredPath(path);'''
if old not in s: raise SystemExit('Normalização antiga não localizada')
s=s.replace(old,new,1)

anchor='''    private static int CertificateFolders(string[] args)\n    {'''
helper=r'''    private static string NormalizeConfiguredPath(string value)
    {
        if (String.IsNullOrWhiteSpace(value)) return "";
        string path = value.Trim().Trim('"').Replace('/', '\\');
        bool unc = path.StartsWith("\\\\", StringComparison.Ordinal);
        string body = unc ? path.Substring(2) : path;
        while (body.IndexOf("\\\\", StringComparison.Ordinal) >= 0) body = body.Replace("\\\\", "\\");
        path = unc ? "\\\\" + body : body;
        try { path = Path.GetFullPath(path); } catch { }
        string root = "";
        try { root = Path.GetPathRoot(path) ?? ""; } catch { }
        if (!String.Equals(path, root, StringComparison.OrdinalIgnoreCase)) path = path.TrimEnd('\\');
        return path;
    }

'''
if anchor not in s: raise SystemExit('CertificateFolders não localizado')
s=s.replace(anchor,helper+anchor,1)
s=s.rstrip()+"\n// "+MARK+" — caminhos canônicos sem barras duplicadas e com UNC preservado.\n"
p.write_text(s,encoding='utf-8',newline='\n')
print('3.13.0: caminhos locais/UNC normalizados no gerenciador de certificados.')
