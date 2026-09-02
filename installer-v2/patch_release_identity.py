from __future__ import annotations
import json
import re
import sys
from pathlib import Path

APP_VERSION = '3.8.0'
BUILD_NAME = 'Motor Fiscal de Devolução 1.2'
MARKER = 'CSM_RELEASE_IDENTITY_3_8_0'


def patch_app(app: Path) -> int:
    text = app.read_text(encoding='utf-8')
    original = text
    # Atualiza apenas identificadores de versão do aplicativo / tela Sobre.
    patterns = [
        (r"(?i)(APP_VERSION\s*=\s*['\"])3\.7\.8(?:\.\d+)?(['\"])", rf"\g<1>{APP_VERSION}\g<2>"),
        (r"(?i)(CURRENT_VERSION\s*=\s*['\"])3\.7\.8(?:\.\d+)?(['\"])", rf"\g<1>{APP_VERSION}\g<2>"),
        (r"(?i)(VERSION\s*=\s*['\"])3\.7\.8(?:\.\d+)?(['\"])", rf"\g<1>{APP_VERSION}\g<2>"),
        (r"(?i)(version\s*:\s*['\"])3\.7\.8(?:\.\d+)?(['\"])", rf"\g<1>{APP_VERSION}\g<2>"),
        (r"(?i)(Versão\s+)3\.7\.8(?:\.\d+)?", rf"\g<1>{APP_VERSION}"),
    ]
    changed = 0
    for pattern, repl in patterns:
        text, n = re.subn(pattern, repl, text)
        changed += n

    # Fallback seguro para builds antigos onde a versão aparece apenas como texto
    # na tela Sobre, sem alterar URLs históricos de releases.
    if changed == 0 and '3.7.8' in text:
        before = text.count('3.7.8')
        text = text.replace("'3.7.8'", f"'{APP_VERSION}'").replace('"3.7.8"', f'"{APP_VERSION}"')
        text = text.replace('Versão 3.7.8', f'Versão {APP_VERSION}')
        changed += before - text.count('3.7.8')

    if MARKER not in text:
        text = text.rstrip() + f"\n// {MARKER} — {APP_VERSION} — {BUILD_NAME}\n"

    if text == original:
        raise SystemExit('Nenhuma identidade de versão foi aplicada ao app.js')
    app.write_text(text, encoding='utf-8', newline='\n')
    print(f'Identidade do aplicativo atualizada para {APP_VERSION}; ocorrências ajustadas: {changed}')
    return changed


def main() -> int:
    if len(sys.argv) != 3:
        print('uso: patch_release_identity.py <pasta-web> <pasta-csm>', file=sys.stderr)
        return 2
    web = Path(sys.argv[1])
    csm = Path(sys.argv[2])
    app = web / 'app.js'
    if not app.is_file():
        raise SystemExit(f'app.js não encontrado em {web}')
    patch_app(app)
    csm.mkdir(parents=True, exist_ok=True)
    payload_root = web.parent.parent
    version_file = payload_root / 'VERSION.txt'
    version_file.write_text(
        f'CSM Visualizador XML {APP_VERSION}\nMotor Fiscal de Devolução 1.2.0\nInstalador completo\n',
        encoding='utf-8',
        newline='\n',
    )
    info = {
        'product': 'CSM Visualizador XML',
        'version': APP_VERSION,
        'build': BUILD_NAME,
        'motor_devolucao': '1.2.0',
        'complete_installer': True,
        'base_runtime': '3.7.8',
    }
    (csm / 'build-info.json').write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding='utf-8')
    final = app.read_text(encoding='utf-8')
    if MARKER not in final or APP_VERSION not in final:
        raise SystemExit('Falha ao validar identidade 3.8.0 no app.js')
    if APP_VERSION not in version_file.read_text(encoding='utf-8'):
        raise SystemExit('VERSION.txt não foi atualizado para 3.8.0')
    print('build-info.json e VERSION.txt criados; versão final 3.8.0 validada')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
