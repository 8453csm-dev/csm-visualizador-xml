from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent
BLUE = '#0F3B66'
BLUE2 = '#174F82'
GREEN = '#28A96B'
WHITE = '#FFFFFF'
MUTED = '#C9D8E6'

def font(size, bold=False):
    candidates = [
        Path('C:/Windows/Fonts/segoeuib.ttf' if bold else 'C:/Windows/Fonts/segoeui.ttf'),
        Path('C:/Windows/Fonts/arialbd.ttf' if bold else 'C:/Windows/Fonts/arial.ttf'),
    ]
    for p in candidates:
        if p.exists(): return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()

def wizard():
    im = Image.new('RGB', (164, 314), BLUE)
    d = ImageDraw.Draw(im)
    for y in range(314):
        t = y/313
        c1 = (15,59,102); c2 = (23,79,130)
        c = tuple(int(a+(b-a)*t) for a,b in zip(c1,c2))
        d.line((0,y,164,y), fill=c)
    d.rounded_rectangle((22,32,142,152), radius=24, fill=WHITE)
    d.text((50,54), '</>', font=font(34, True), fill=BLUE)
    d.rectangle((22,142,142,152), fill=GREEN)
    d.text((22,181), 'CSM', font=font(30, True), fill=WHITE)
    d.text((22,221), 'Visualizador', font=font(18, True), fill=WHITE)
    d.text((22,246), 'XML', font=font(28, True), fill=GREEN)
    d.text((22,288), 'Instalação segura', font=font(10), fill=MUTED)
    im.save(OUT/'wizard.bmp')

def small():
    im = Image.new('RGB', (55,55), WHITE)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((2,2,52,52), radius=12, fill=BLUE)
    d.text((10,12), '</>', font=font(18, True), fill=WHITE)
    d.rectangle((8,43,47,47), fill=GREEN)
    im.save(OUT/'wizard-small.bmp')

def normalize_installer_script():
    """Mantém o instalador no mesmo perfil do usuário que executa o CSM.

    O produto usa LocalAppData/HKCU/atalhos do usuário. Pedir elevação UAC faria
    essas áreas apontarem para o usuário administrador informado na credencial,
    podendo deixar o usuário original preso a um atalho/versão antiga.
    """
    iss = OUT / 'CSMVisualizadorXML.iss'
    if not iss.exists():
        raise SystemExit(f'Arquivo do instalador não encontrado: {iss}')
    text = iss.read_text(encoding='utf-8')
    text = text.replace('PrivilegesRequired=admin', 'PrivilegesRequired=lowest')
    text = text.replace('WizardResizable=no\n', '')
    text = text.replace('UninstallDisplayVersion={#AppVersion}\n', '')
    iss.write_text(text, encoding='utf-8', newline='\n')
    final = iss.read_text(encoding='utf-8')
    if 'PrivilegesRequired=lowest' not in final:
        raise SystemExit('Instalador não foi normalizado para instalação per-user')
    if 'PrivilegesRequired=admin' in final:
        raise SystemExit('Instalador ainda solicita administrador indevidamente')
    print('Installer normalized: per-user, sem UAC e sem diretivas obsoletas')

wizard(); small(); normalize_installer_script()
print('Brand assets generated')
