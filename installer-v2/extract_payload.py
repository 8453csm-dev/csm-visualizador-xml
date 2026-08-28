from pathlib import Path
import hashlib, io, re, shutil, struct, sys, zipfile

BASE_SHA = 'd6086b661fb40d4c05ce76d38ecec836a8ff7d5c4c55a6df35c68ed03b484b74'
MARK_RE = re.compile(rb'(?s)<!-- CSM_XML_ENHANCER_V[1-8] -->.*?<!-- /CSM_XML_ENHANCER_V[1-8] -->')

base = Path(sys.argv[1])
enhancer = Path(sys.argv[2]).read_bytes()
out = Path(sys.argv[3])

raw = base.read_bytes()
sha = hashlib.sha256(raw).hexdigest()
if sha != BASE_SHA:
    raise SystemExit(f'SHA-256 base inesperado: {sha}')

eocd = raw.rfind(b'PK\x05\x06')
if eocd < 0:
    raise SystemExit('EOCD ZIP não encontrado no instalador base')
_, _, _, _, total, cd_size, cd_off, comment_len = struct.unpack_from('<4s4H2LH', raw, eocd)
zip_start = eocd - cd_size - cd_off
zip_end = eocd + 22 + comment_len
if zip_start < 0 or zip_end > len(raw):
    raise SystemExit('Limites do ZIP interno inválidos')

chunk = raw[zip_start:zip_end]
with zipfile.ZipFile(io.BytesIO(chunk)) as z:
    bad = z.testzip()
    if bad:
        raise SystemExit(f'Arquivo corrompido no payload: {bad}')
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    root = out.resolve()
    for info in z.infolist():
        dest = (out / info.filename).resolve()
        if root not in dest.parents and dest != root:
            raise SystemExit(f'Caminho inseguro no ZIP: {info.filename}')
    z.extractall(out)

exe = out / 'CSM Visualizador XML.exe'
ico = out / '_internal' / 'assets' / 'CSMVisualizadorXML.ico'
if not exe.is_file():
    raise SystemExit('Executável principal não encontrado no payload extraído')
if not ico.is_file():
    raise SystemExit('Ícone do aplicativo não encontrado no payload extraído')

patched = 0
for p in out.rglob('*'):
    if not p.is_file() or p.suffix.lower() not in ('.html', '.htm'):
        continue
    low_path = p.as_posix().lower()
    if any(x in low_path for x in ('/pdfjs/', '/pdf.js/', '/webview2/', '/edge/', '/runtime/', '/node_modules/')):
        continue
    data = p.read_bytes()
    cleaned = MARK_RE.sub(b'', data)
    idx = cleaned.lower().rfind(b'</body>')
    if idx < 0:
        continue
    merged = cleaned[:idx] + b'\n' + enhancer + b'\n' + cleaned[idx:]
    if merged != data:
        p.write_bytes(merged)
        patched += 1

if patched == 0:
    raise SystemExit('Nenhum HTML recebeu a Aba XML v8')

print(f'Payload extraído: {total} entradas ZIP')
print(f'ZIP interno SHA256: {hashlib.sha256(chunk).hexdigest()}')
print(f'HTMLs atualizados com Aba XML v8: {patched}')
print(f'Executável principal: {exe} ({exe.stat().st_size} bytes)')
