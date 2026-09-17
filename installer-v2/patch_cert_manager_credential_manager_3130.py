from pathlib import Path

p=Path('installer-v2/launcher/csm_fiscal_core.cs')
s=p.read_text(encoding='utf-8')
MARK='CSM_CREDENTIAL_MANAGER_WRITE_3130'
if MARK in s:
    print('Credential Manager write 3.13.0 já aplicado')
    raise SystemExit(0)
if 'CSM_CERT_MANAGER_3130' not in s:
    raise SystemExit('Aplique o gerenciador A1 antes')

old='''    [DllImport("advapi32.dll", EntryPoint = "CredReadW", CharSet = CharSet.Unicode, SetLastError = true)]\n    private static extern bool CredRead(string target, uint type, int reservedFlag, out IntPtr credentialPtr);\n    [DllImport("advapi32.dll", SetLastError = true)]\n    private static extern void CredFree(IntPtr credentialPtr);'''
new='''    [DllImport("advapi32.dll", EntryPoint = "CredReadW", CharSet = CharSet.Unicode, SetLastError = true)]\n    private static extern bool CredRead(string target, uint type, int reservedFlag, out IntPtr credentialPtr);\n    [DllImport("advapi32.dll", EntryPoint = "CredWriteW", CharSet = CharSet.Unicode, SetLastError = true)]\n    private static extern bool CredWrite(ref CREDENTIAL credential, uint flags);\n    [DllImport("advapi32.dll", SetLastError = true)]\n    private static extern void CredFree(IntPtr credentialPtr);'''
if old not in s: raise SystemExit('P/Invoke CredRead não localizado')
s=s.replace(old,new,1)

anchor='''    private static string ReadCredential(string target)\n    {'''
if anchor not in s: raise SystemExit('ReadCredential ausente')
helper=r'''    private static string CredentialTargetFor(string thumbprint)
    {
        string clean = Regex.Replace((thumbprint ?? "").ToUpperInvariant(), "[^A-F0-9]", "");
        return String.IsNullOrEmpty(clean) ? "" : "CSM.VisualizadorXML.A1." + clean;
    }

    private static bool WriteCredential(string target, string secret)
    {
        if (String.IsNullOrWhiteSpace(target)) return false;
        byte[] blob = Encoding.Unicode.GetBytes(secret ?? "");
        IntPtr targetPtr = IntPtr.Zero, userPtr = IntPtr.Zero, blobPtr = IntPtr.Zero;
        try
        {
            targetPtr = Marshal.StringToCoTaskMemUni(target);
            userPtr = Marshal.StringToCoTaskMemUni("CSM Visualizador XML");
            if (blob.Length > 0)
            {
                blobPtr = Marshal.AllocHGlobal(blob.Length);
                Marshal.Copy(blob, 0, blobPtr, blob.Length);
            }
            CREDENTIAL c = new CREDENTIAL();
            c.Type = 1; // CRED_TYPE_GENERIC
            c.TargetName = targetPtr;
            c.CredentialBlobSize = (uint)blob.Length;
            c.CredentialBlob = blobPtr;
            c.Persist = 2; // CRED_PERSIST_LOCAL_MACHINE
            c.UserName = userPtr;
            return CredWrite(ref c, 0);
        }
        catch { return false; }
        finally
        {
            if (targetPtr != IntPtr.Zero) Marshal.FreeCoTaskMem(targetPtr);
            if (userPtr != IntPtr.Zero) Marshal.FreeCoTaskMem(userPtr);
            if (blobPtr != IntPtr.Zero) Marshal.FreeHGlobal(blobPtr);
            Array.Clear(blob, 0, blob.Length);
        }
    }

    private static void StoreProtectedPassword(CertRecord rec, string password)
    {
        rec.CredentialTarget = CredentialTargetFor(rec.Thumbprint);
        if (!String.IsNullOrWhiteSpace(rec.CredentialTarget) && WriteCredential(rec.CredentialTarget, password ?? ""))
        {
            rec.PasswordDpapiB64 = "";
            return;
        }
        rec.CredentialTarget = "";
        rec.PasswordDpapiB64 = ProtectSecret(password ?? "");
    }

'''
s=s.replace(anchor,helper+anchor,1)

old='''        string saved = prior == null ? "" : UnprotectSecret(prior.PasswordDpapiB64);'''
new='''        string saved = prior == null ? "" : ReadCredential(prior.CredentialTarget);\n        if (String.IsNullOrEmpty(saved) && prior != null) saved = UnprotectSecret(prior.PasswordDpapiB64);'''
if old not in s: raise SystemExit('senha salva do scanner não localizada')
s=s.replace(old,new,1)

old='''            FillCertificateMetadata(rec, cert);\n            if (!String.IsNullOrEmpty(accepted)) rec.PasswordDpapiB64 = ProtectSecret(accepted);\n            else if (prior != null) rec.PasswordDpapiB64 = prior.PasswordDpapiB64;'''
new='''            FillCertificateMetadata(rec, cert);\n            if (!String.IsNullOrEmpty(accepted)) StoreProtectedPassword(rec, accepted);\n            else if (prior != null) { rec.CredentialTarget = prior.CredentialTarget; rec.PasswordDpapiB64 = prior.PasswordDpapiB64; }'''
if old not in s: raise SystemExit('persistência no scanner não localizada')
s=s.replace(old,new,1)

old='''            FillCertificateMetadata(rec, cert);\n            rec.PasswordDpapiB64 = ProtectSecret(password ?? "");'''
new='''            FillCertificateMetadata(rec, cert);\n            StoreProtectedPassword(rec, password ?? "");'''
if old not in s: raise SystemExit('persistência no validate não localizada')
s=s.replace(old,new,1)

s=s.rstrip()+"\n// "+MARK+" — CredWriteW primário e DPAPI fallback; senha nunca serializada em claro.\n"
p.write_text(s,encoding='utf-8',newline='\n')
print('3.13.0: senhas A1 persistidas no Credential Manager com DPAPI fallback.')
