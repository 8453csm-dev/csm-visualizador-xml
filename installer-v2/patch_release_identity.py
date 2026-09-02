from __future__ import annotations
import json
import re
import sys
from pathlib import Path

APP_VERSION = '3.8.1'
BUILD_NAME = 'Motor Fiscal de Devolução 1.3'
MARKER = 'CSM_RELEASE_IDENTITY_3_8_1'
MOTOR_VERSION = '1.3.0'


def patch_text(text: str) -> tuple[str, int]:
    patterns = [
        (r"(?i)(APP_VERSION\s*=\s*['\"])(?:3\.7\.8|3\.8\.0)(?:\.\d+)?(['\"])", rf"\g<1>{APP_VERSION}\g<2>"),
        (r"(?i)(CURRENT_VERSION\s*=\s*['\"])(?:3\.7\.8|3\.8\.0)(?:\.\d+)?(['\"])", rf"\g<1>{APP_VERSION}\g<2>"),
        (r"(?i)(\bappVersion\b\s*[:=]\s*['\"])(?:3\.7\.8|3\.8\.0)(?:\.\d+)?(['\"])", rf"\g<1>{APP_VERSION}\g<2>"),
        (r"(?i)(\bcurrentVersion\b\s*[:=]\s*['\"])(?:3\.7\.8|3\.8\.0)(?:\.\d+)?(['\"])", rf"\g<1>{APP_VERSION}\g<2>"),
        (r"(?i)(\bVERSION\b\s*=\s*['\"])(?:3\.7\.8|3\.8\.0)(?:\.\d+)?(['\"])", rf"\g<1>{APP_VERSION}\g<2>"),
        (r"(?i)(\bversion\b\s*:\s*['\"])(?:3\.7\.8|3\.8\.0)(?:\.\d+)?(['\"])", rf"\g<1>{APP_VERSION}\g<2>"),
        (r"(?i)(data-version\s*=\s*['\"])(?:3\.7\.8|3\.8\.0)(?:\.\d+)?(['\"])", rf"\g<1>{APP_VERSION}\g<2>"),
        (r"(?i)(Versão\s+)(?:3\.7\.8|3\.8\.0)(?:\.\d+)?", rf"\g<1>{APP_VERSION}"),
        (r"(?i)(Versao\s+)(?:3\.7\.8|3\.8\.0)(?:\.\d+)?", rf"\g<1>{APP_VERSION}"),
    ]
    changed = 0
    for pattern, repl in patterns:
        text, n = re.subn(pattern, repl, text)
        changed += n
    return text, changed


def patch_about_runtime(text: str) -> tuple[str, int]:
    changed = 0
    patterns = [
        (
            r"els\.aboutVersion\.textContent\s*=\s*`Versão\s+\$\{r\?\.version\|\|['\"]3\.0\.1['\"]\}`",
            f"els.aboutVersion.textContent='Versão {APP_VERSION}'",
        ),
        (
            r"els\.aboutVersion\.textContent\s*=\s*`Versão\s+\$\{r\.current\|\|['\"](?:3\.7\.8|3\.8\.0|3\.8\.1)['\"]\}`",
            f"els.aboutVersion.textContent='Versão {APP_VERSION}'",
        ),
    ]
    for pattern, repl in patterns:
        text, n = re.subn(pattern, repl, text)
        changed += n
    if f"els.aboutVersion.textContent='Versão {APP_VERSION}'" not in text:
        raise SystemExit('Não foi possível localizar/corrigir a origem real da versão no modal Sobre')
    return text, changed


def patch_frontend(web: Path) -> int:
    total = 0
    touched: list[str] = []
    for path in sorted(web.rglob('*')):
        if not path.is_file() or path.suffix.lower() not in {'.js', '.html', '.css', '.json'}:
            continue
        try:
            text = path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            continue
        updated, changed = patch_text(text)
        if path.name.lower() == 'app.js':
            updated, about_changed = patch_about_runtime(updated)
            changed += about_changed
        if changed:
            path.write_text(updated, encoding='utf-8', newline='\n')
            total += changed
            touched.append(f'{path.name}:{changed}')
    print('Identidade 3.8.1 aplicada no frontend:', ', '.join(touched) if touched else 'nenhum arquivo adicional')
    return total


def validate_no_visible_old_version(web: Path) -> None:
    offenders: list[str] = []
    visible_old = re.compile(r'(?i)(Versão|Versao)\s+(?:3\.7\.8|3\.8\.0)(?:\.\d+)?')
    version_binding_old = re.compile(
        r"(?i)(APP_VERSION|CURRENT_VERSION|appVersion|currentVersion|\bVERSION\b|data-version)"
        r"[^\n]{0,40}(?:3\.7\.8|3\.8\.0)(?:\.\d+)?"
    )
    for path in sorted(web.rglob('*')):
        if not path.is_file() or path.suffix.lower() not in {'.js', '.html', '.css', '.json'}:
            continue
        try:
            text = path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            continue
        if visible_old.search(text) or version_binding_old.search(text):
            offenders.append(str(path.relative_to(web)))
    if offenders:
        raise SystemExit('Versão antiga ainda pode ser exibida no frontend: ' + ', '.join(offenders))

    app = web / 'app.js'
    app_text = app.read_text(encoding='utf-8')
    expected = f"els.aboutVersion.textContent='Versão {APP_VERSION}'"
    if app_text.count(expected) < 2:
        raise SystemExit('Modal Sobre e verificação automática não estão fixados na versão 3.8.1')
    if re.search(r"aboutVersion\.textContent\s*=\s*`Versão\s+\$\{[^}]*?(?:version|current)", app_text):
        raise SystemExit('A versão visível ainda depende do backend antigo')


def main() -> int:
    if len(sys.argv) != 3:
        print('uso: patch_release_identity.py <pasta-web> <pasta-csm>', file=sys.stderr)
        return 2
    web = Path(sys.argv[1])
    csm = Path(sys.argv[2])
    app = web / 'app.js'
    if not app.is_file():
        raise SystemExit(f'app.js não encontrado em {web}')

    changed = patch_frontend(web)
    text = app.read_text(encoding='utf-8')
    if MARKER not in text:
        text = text.rstrip() + f"\n// {MARKER} — {APP_VERSION} — {BUILD_NAME}\n"
        app.write_text(text, encoding='utf-8', newline='\n')
    if changed == 0:
        print('Aviso: nenhuma ocorrência antiga precisou ser substituída; identidade será validada pelo marcador e build-info.')

    validate_no_visible_old_version(web)
    csm.mkdir(parents=True, exist_ok=True)
    payload_root = web.parent.parent
    version_file = payload_root / 'VERSION.txt'
    version_file.write_text(
        f'CSM Visualizador XML {APP_VERSION}\nMotor Fiscal de Devolução {MOTOR_VERSION}\nInstalador completo\n',
        encoding='utf-8', newline='\n'
    )
    info = {
        'product': 'CSM Visualizador XML',
        'version': APP_VERSION,
        'build': BUILD_NAME,
        'motor_devolucao': MOTOR_VERSION,
        'complete_installer': True,
        'base_runtime': '3.7.8',
        'entrypoint_deterministic': True,
    }
    (csm / 'build-info.json').write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding='utf-8')

    final = app.read_text(encoding='utf-8')
    if MARKER not in final:
        raise SystemExit('Falha ao validar marcador de identidade 3.8.1 no app.js')
    if APP_VERSION not in version_file.read_text(encoding='utf-8'):
        raise SystemExit('VERSION.txt não foi atualizado para 3.8.1')
    print('build-info.json, VERSION.txt e modal Sobre validados como versão 3.8.1')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
