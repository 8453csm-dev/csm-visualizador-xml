from pathlib import Path

p=Path('installer-v2/launcher/csm_fiscal_core.cs')
s=p.read_text(encoding='utf-8')
MARK='CSM_CERT_PUBLIC_IDS_3130'
if MARK in s:
    print('IDs públicos de certificados 3.13.0 já aplicados')
    raise SystemExit(0)
if 'CSM_CERT_MANAGER_3130' not in s:
    raise SystemExit('Aplique o gerenciador de certificados antes')

anchor='''    private static Dictionary<string, object> PublicCertificate(CertRecord c)\n    {'''
if anchor not in s: raise SystemExit('PublicCertificate ausente')
helper=r'''    private static string CertificateRecordId(string path)
    {
        using (SHA256 sha = SHA256.Create())
        {
            byte[] raw = sha.ComputeHash(Encoding.UTF8.GetBytes((path ?? "").ToUpperInvariant()));
            return BitConverter.ToString(raw).Replace("-", "").Substring(0, 24);
        }
    }

    private static string PublicFileName(string path)
    {
        if (String.IsNullOrWhiteSpace(path)) return "";
        string ext = Path.GetExtension(path) ?? "";
        return FileLabel(path) + ext;
    }

'''
s=s.replace(anchor,helper+anchor,1)

old='''            {"cnpj", c.Cnpj ?? ""}, {"empresa", c.Empresa ?? ""}, {"path", c.Path ?? ""},\n            {"expiry", c.Expiry ?? ""}, {"not_before", c.NotBefore ?? ""}, {"days_remaining", c.DaysRemaining},'''
new='''            {"id", CertificateRecordId(c.Path)}, {"cnpj", c.Cnpj ?? ""}, {"empresa", c.Empresa ?? ""}, {"file_name", PublicFileName(c.Path)},\n            {"expiry", c.Expiry ?? ""}, {"not_before", c.NotBefore ?? ""}, {"days_remaining", c.DaysRemaining},'''
if old not in s: raise SystemExit('PublicCertificate path não localizado')
s=s.replace(old,new,1)

# Permite validar por ID opaco sem expor path ao frontend.
old='''        string path = Arg(args,"--path");\n        if (String.IsNullOrWhiteSpace(path) || !File.Exists(path)) return WriteError("Arquivo A1 não encontrado.", 34);'''
new='''        string path = Arg(args,"--path");\n        string publicId = Arg(args,"--id");\n        if (String.IsNullOrWhiteSpace(path) && !String.IsNullOrWhiteSpace(publicId))\n        {\n            CertRecord known = LoadAllCertificateRecords().FirstOrDefault(x => String.Equals(CertificateRecordId(x.Path), publicId, StringComparison.OrdinalIgnoreCase));\n            if (known != null) path = known.Path;\n        }\n        if (String.IsNullOrWhiteSpace(path) || !File.Exists(path)) return WriteError("Arquivo A1 não encontrado.", 34);'''
if old not in s: raise SystemExit('CertificateCommand path não localizado')
s=s.replace(old,new,1)

s=s.rstrip()+"\n// "+MARK+" — frontend recebe ID opaco; caminho real/candidato de senha permanece no Fiscal Core.\n"
p.write_text(s,encoding='utf-8',newline='\n')
print('3.13.0: caminhos dos A1 ocultados da API pública; IDs opacos habilitados.')
