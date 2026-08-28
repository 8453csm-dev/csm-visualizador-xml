from pathlib import Path
import io,re,zipfile
p=Path('temp/CSMVisualizadorXML-3.7.8-Instalador-Completo.exe')
b=p.read_bytes()
for magic,name in [(b'PK\x03\x04','ZIP local'),(b'PK\x05\x06','ZIP EOCD'),(b'MZ','PE/MZ'),(b'7z\xbc\xaf\x27\x1c','7z'),(b'\x1f\x8b','gzip')]:
    pos=[]; start=0
    while True:
        i=b.find(magic,start)
        if i<0: break
        pos.append(i); start=i+1
    print(name,'count=',len(pos),'first=',pos[:30])
starts=[]; s=0
while True:
    i=b.find(b'PK\x03\x04',s)
    if i<0: break
    starts.append(i); s=i+1
for i in starts:
    try:
        z=zipfile.ZipFile(io.BytesIO(b[i:]))
        names=z.namelist()
        if names:
            print('VALID_ZIP_AT',i,'files',len(names),'sample',names[:40])
            out=Path('temp/extracted'); out.mkdir(exist_ok=True)
            z.extractall(out)
            break
    except Exception:
        pass
strings=re.findall(rb'[ -~]{6,}',b)
keys=[b'CSM',b'Visualizador',b'payload',b'zip',b'install',b'shortcut',b'LocalAppData',b'ProgramFiles',b'python',b'webview',b'extract',b'desktop',b'self-test']
n=0
for x in strings:
    lx=x.lower()
    if any(k.lower() in lx for k in keys):
        print('STR',x[:400].decode('ascii','ignore'))
        n+=1
        if n>=180: break
