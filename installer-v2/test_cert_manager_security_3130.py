import json
import os
import pathlib
import subprocess
import tempfile

ROOT=pathlib.Path(__file__).resolve().parents[1]
SRC=ROOT/'installer-v2'/'launcher'/'csm_fiscal_core.cs'


def run(cmd, **kw):
    return subprocess.run(cmd, text=True, capture_output=True, **kw)


def compile_core(out):
    fx=pathlib.Path(os.environ['WINDIR'])/'Microsoft.NET'/'Framework64'/'v4.0.30319'
    cmd=[str(fx/'csc.exe'),'/nologo','/target:exe','/optimize+','/platform:x64',f'/out:{out}',
         f'/reference:{fx/"System.Web.Extensions.dll"}',f'/reference:{fx/"System.Security.dll"}',f'/reference:{fx/"System.Xml.Linq.dll"}',str(SRC)]
    p=run(cmd)
    if p.returncode: raise AssertionError(p.stdout+p.stderr)


def jrun(exe,args,env,stdin=None,fail_ok=False):
    p=run([str(exe)]+args,env=env,input=stdin)
    raw=(p.stdout or '').strip()
    data=json.loads(raw) if raw else {}
    if not fail_ok and p.returncode: raise AssertionError((args,p.returncode,raw,p.stderr))
    return p,data,raw


def make_pfx(path,password):
    ps=f'''$p=ConvertTo-SecureString '{password}' -AsPlainText -Force;
$c=New-SelfSignedCertificate -Subject 'CN=FRAMEL INDUSTRIA E COMERCIO DE DOCES LTDA' -CertStoreLocation 'Cert:\\CurrentUser\\My' -KeyAlgorithm RSA -KeyLength 2048 -KeyExportPolicy Exportable -NotAfter (Get-Date).AddYears(1);
Export-PfxCertificate -Cert $c -FilePath '{str(path).replace("'","''")}' -Password $p | Out-Null;
Remove-Item ('Cert:\\CurrentUser\\My\\'+$c.Thumbprint) -Force;
'''
    p=run(['powershell','-NoProfile','-NonInteractive','-Command',ps])
    if p.returncode or not path.exists(): raise AssertionError(p.stdout+p.stderr)


def main():
    with tempfile.TemporaryDirectory(prefix='csm-cert-sec-') as td:
        t=pathlib.Path(td); local=t/'local'; local.mkdir(); env=dict(os.environ); env['LOCALAPPDATA']=str(local)
        exe=t/'FiscalCore.exe'; compile_core(exe)
        folder=t/'certs'; folder.mkdir(); pfx=folder/'FRAMEL - 1234.pfx'; make_pfx(pfx,'1234')
        jrun(exe,['folders','add','--path',str(folder)],env)
        p,data,raw=jrun(exe,['scan'],env)
        assert data.get('ok') is True, data
        certs=data.get('certificates') or []; assert len(certs)==1,certs
        c=certs[0]
        assert c.get('id'),c
        assert c.get('file_name')=='FRAMEL.pfx',c
        assert 'path' not in c,c
        assert '1234' not in raw,'senha do nome do arquivo vazou na API pública'
        assert c.get('has_protected_credential') is True,c
        assert c.get('status') in ('Válido','Vencendo'),c
        idx=local/'CSM Visualizador XML'/'certificados'/'certificados.json'
        stored=idx.read_text(encoding='utf-8')
        # O caminho original pode conter o padrão legado; a senha nunca pode existir como campo próprio.
        parsed=json.loads(stored); row=parsed[0]
        assert 'password' not in row and 'senha' not in row
        assert row.get('credential_target') or row.get('password_dpapi_b64'),row
        assert row.get('password_dpapi_b64','') != '1234'

        # Validação manual usa ID opaco + stdin; senha errada falha sem ecoar segredo.
        q,d,rawbad=jrun(exe,['cert','validate','--id',c['id']],env,stdin='errada',fail_ok=True)
        assert q.returncode!=0
        assert 'errada' not in rawbad
        assert 'Senha inválida' in str(d.get('message',''))

        q,d,rawgood=jrun(exe,['cert','validate','--id',c['id']],env,stdin='1234')
        assert d.get('ok') is True,d
        assert '1234' not in rawgood
        assert 'path' not in (d.get('certificate') or {}),d
        print('OK - PFX real, senha por filename, Credential Manager/DPAPI e API sanitizada.')

if __name__=='__main__': main()
