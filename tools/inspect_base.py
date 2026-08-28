from pathlib import Path
import io,re,struct,zipfile
p=Path('temp/CSMVisualizadorXML-3.7.8-Instalador-Completo.exe')
b=p.read_bytes()
for magic,name in [(b'PK\x03\x04','ZIP local'),(b'PK\x05\x06','ZIP EOCD'),(b'MZ','PE/MZ')]:
    pos=[]; start=0
    while True:
        i=b.find(magic,start)
        if i<0: break
        pos.append(i); start=i+1
    print(name,'count=',len(pos),'first=',pos[:30])
eocd=b.rfind(b'PK\x05\x06')
if eocd>=0:
    sig,disk,cd_disk,n_disk,n_total,cd_size,cd_off,comment_len=struct.unpack_from('<4s4H2LH',b,eocd)
    zip_start=eocd-cd_size-cd_off
    zip_end=eocd+22+comment_len
    print('EOCD',eocd,'entries',n_total,'cd_size',cd_size,'cd_off',cd_off,'zip_start',zip_start,'zip_end',zip_end)
    chunk=b[zip_start:zip_end]
    try:
        z=zipfile.ZipFile(io.BytesIO(chunk))
        names=z.namelist()
        print('VALID_ZIP_FROM_EOCD files',len(names),'sample',names[:50])
        out=Path('temp/extracted'); out.mkdir(exist_ok=True)
        z.extractall(out)
        Path('temp/payload.zip').write_bytes(chunk)
        print('PAYLOAD_ZIP_SHA256')
        import hashlib
        print(hashlib.sha256(chunk).hexdigest())
    except Exception as exc:
        print('EOCD_ZIP_ERROR',repr(exc))
strings=re.findall(rb'[ -~]{6,}',b)
keys=[b'CSM',b'Visualizador',b'payload',b'install',b'shortcut',b'LocalAppData',b'ProgramFiles',b'desktop',b'uninstall']
n=0
for x in strings:
    lx=x.lower()
    if any(k.lower() in lx for k in keys):
        print('STR',x[:400].decode('ascii','ignore'))
        n+=1
        if n>=100: break
