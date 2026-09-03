from pathlib import Path
import re
p=Path('installer-v2/CSMVisualizadorXML.iss')
s=p.read_text(encoding='utf-8')
s=re.sub(r'#define AppVersion "3\.[0-9]+\.[0-9]+"','#define AppVersion "3.9.1"',s)
s=re.sub(r'OutputBaseFilename=CSMVisualizadorXML-3\.[0-9]+\.[0-9]+-Instalador-Completo','OutputBaseFilename=CSMVisualizadorXML-3.9.1-Instalador-Completo',s)
s=re.sub(r'VersionInfoDescription=Instalador completo do CSM Visualizador XML [^\r\n]*','VersionInfoDescription=Instalador completo do CSM Visualizador XML 3.9.1 com Entender a Tributação corrigido e Motor Fiscal de Devolução',s)
s=re.sub(r'VersionInfoVersion=3\.[0-9]+\.[0-9]+\.0','VersionInfoVersion=3.9.1.0',s)
s=s.replace('PrivilegesRequired=admin','PrivilegesRequired=lowest')
s=re.sub(r'CSM Visualizador XML 3\.[0-9]+\.[0-9]+','CSM Visualizador XML 3.9.1',s)
s=re.sub(r'versão 3\.[0-9]+\.[0-9]+','versão 3.9.1',s,flags=re.I)
welcome="""WizardForm.WelcomeLabel2.Caption :=
    'Instalador completo — funciona também em computadores que nunca tiveram o CSM Visualizador XML.' + #13#10 + #13#10 +
    'NOVIDADES DA VERSÃO 3.9.1' + #13#10 +
    '• CORREÇÃO: Entender a Tributação não congela mais a interface ao abrir' + #13#10 +
    '• A análise tributária é executada somente quando solicitada, sem ciclo de renderização' + #13#10 +
    '• Mantida a explicação de ICMS, redução, MVA/IVA-ST, ICMS-ST, IPI, FCP, DIFAL, PIS e COFINS' + #13#10 +
    '• Mantidos detalhamento técnico, conferência automática e relatório para o cliente' + #13#10 + #13#10 +
    'MANTÉM TUDO DA VERSÃO ANTERIOR' + #13#10 +
    '• Motor Fiscal de Devolução total/parcial e referência por item' + #13#10 +
    '• Abertura de vários XMLs em abas na mesma janela' + #13#10 +
    '• Localizador Fiscal e Consulta DANFE' + #13#10 +
    '• Tema claro/escuro, Aba XML avançada e associação .xml' + #13#10 +
    '• Instalação limpa, atalho na Área de Trabalho e desinstalador' + #13#10 + #13#10 +
    'O instalador removerá versões antigas antes de instalar a 3.9.1.';"""
s,n=re.subn(r"WizardForm\.WelcomeLabel2\.Caption\s*:=.*?;\n\s*WizardForm\.WelcomeLabel2\.Font\.Color",welcome+'\n  WizardForm.WelcomeLabel2.Font.Color',s,flags=re.S)
if n!=1:raise SystemExit(f'Não consegui atualizar novidades do instalador: {n}')
s=re.sub(r"WizardForm\.FinishedLabel\.Caption := 'CSM Visualizador XML [^']* instalado com sucesso\.';","WizardForm.FinishedLabel.Caption := 'CSM Visualizador XML 3.9.1 instalado com sucesso.';",s)
s=re.sub(r'Tudo pronto para instalar a versão 3\.[0-9]+\.[0-9]+','Tudo pronto para instalar a versão 3.9.1',s)
s=re.sub(r'Instalando CSM Visualizador XML 3\.[0-9]+\.[0-9]+','Instalando CSM Visualizador XML 3.9.1',s)
s=re.sub(r'A versão 3\.[0-9]+\.[0-9]+ foi instalada','A versão 3.9.1 foi instalada',s)
s=re.sub(r'Abrir CSM Visualizador XML 3\.[0-9]+\.[0-9]+','Abrir CSM Visualizador XML 3.9.1',s)
for token in ('#define AppVersion "3.9.1"','OutputBaseFilename=CSMVisualizadorXML-3.9.1-Instalador-Completo','VersionInfoVersion=3.9.1.0','PrivilegesRequired=lowest','Entender a Tributação','Motor Fiscal de Devolução','BrazilianPortuguese.isl'):
    if token not in s:raise SystemExit('Instalador 3.9.1 incompleto: '+token)
if 'PrivilegesRequired=admin' in s:raise SystemExit('Instalador ainda exige administrador')
p.write_text(s,encoding='utf-8',newline='\n')
print('ISS preparado para CSM Visualizador XML 3.9.1.')
