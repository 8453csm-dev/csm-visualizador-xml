import json
import os
import pathlib
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / 'installer-v2' / 'launcher' / 'csm_fiscal_core.cs'


def run(cmd, **kwargs):
    return subprocess.run(cmd, text=True, capture_output=True, **kwargs)


def compile_core(out):
    windir = pathlib.Path(os.environ['WINDIR'])
    fx = windir / 'Microsoft.NET' / 'Framework64' / 'v4.0.30319'
    csc = fx / 'csc.exe'
    refs = [fx/'System.Web.Extensions.dll', fx/'System.Security.dll', fx/'System.Xml.Linq.dll']
    cmd = [str(csc), '/nologo', '/target:exe', '/optimize+', '/platform:x64', f'/out:{out}']
    cmd += [f'/reference:{r}' for r in refs]
    cmd += [str(SRC)]
    p = run(cmd)
    if p.returncode:
        print(p.stdout, p.stderr)
        raise SystemExit('Fiscal Core não compilou')


def jrun(exe, args, env, stdin=None, allow_fail=False):
    p = run([str(exe)] + args, env=env, input=stdin)
    text = (p.stdout or '').strip()
    if not allow_fail and p.returncode != 0:
        raise AssertionError(f'comando falhou {args}: rc={p.returncode} out={text} err={p.stderr}')
    try:
        data = json.loads(text)
    except Exception as e:
        raise AssertionError(f'JSON inválido em {args}: {text!r}') from e
    return p.returncode, data, text


def main():
    with tempfile.TemporaryDirectory(prefix='csm3130-') as td:
        t = pathlib.Path(td)
        exe = t / 'CSM Fiscal Core Test.exe'
        compile_core(exe)
        local = t / 'localappdata'
        local.mkdir()
        env = dict(os.environ)
        env['LOCALAPPDATA'] = str(local)

        rc, data, raw = jrun(exe, ['folders', 'list'], env)
        assert data.get('ok') is True
        assert data.get('folders') == [], data

        certdir = t / 'certificados'
        nested = certdir / 'clientes' / 'framel'
        nested.mkdir(parents=True)
        fake = nested / 'FRAMEL - 1234.pfx'
        fake.write_bytes(b'nao-e-um-pfx')

        rc, data, raw = jrun(exe, ['folders', 'add', '--path', str(certdir)], env)
        assert data.get('ok') is True, data
        folders = data.get('folders') or []
        assert len(folders) == 1, folders
        assert str(folders[0]).lower().rstrip('\\/').endswith('certificados'), folders

        rc, data, raw = jrun(exe, ['scan'], env)
        assert data.get('ok') is True, data
        assert '1234' not in raw, 'senha candidata vazou no JSON público'
        certs = data.get('certificates') or []
        assert len(certs) == 1, certs
        found = certs[0]
        assert found.get('id'), found
        assert found.get('file_name') == 'FRAMEL.pfx', found
        assert 'path' not in found, found
        assert found.get('status') in ('Senha necessária', 'Arquivo inválido'), found
        forbidden = {'password', 'senha', 'password_dpapi_b64'}
        assert not (forbidden & set(found.keys())), found

        rc, data, raw = jrun(exe, ['folders', 'remove', '--path', str(certdir)], env)
        assert data.get('ok') is True
        assert data.get('folders') == [], data

        print('OK - registro de pastas, scan recursivo, ID opaco e sanitização de senha validados.')


if __name__ == '__main__':
    main()
