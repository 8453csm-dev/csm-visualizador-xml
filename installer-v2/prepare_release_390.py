from pathlib import Path
import re
p=Path('installer-v2/CSMVisualizadorXML.iss')
s=p.read_text(encoding='utf-8')
s=re.sub(r'#define AppVersion "3\.8\.[01]"','#define AppVersion "3.9.0"',s)
s=re.sub(r'OutputBaseFilename=CSMVisualizadorXML-3\.8\.[01]-Instalador-Completo','OutputBaseFilename=CSMVisualizadorXML-3.9.0-Instalador-Completo',s)
s=re.sub(r'VersionInfoDescription=Instalador completo do CSM Visualizador XML 3\.8\.[01][^\r\n]*','VersionInfoDescription=Instalador completo do CSM Visualizador XML 3.9.0 com Entender a Tributação e Motor Fiscal de Devolução',s)
s=re.sub(r'VersionInfoVersion=3\.8\.[01]\.0','VersionInfoVersion=3.9.0.0',s)
s=s.replace('PrivilegesRequired=admin','PrivilegesRequired=lowest')
s=re.sub(r'CSM Visualizador XML 3\.8\.[01]', 'CSM Visualizador XML 3.9.0', s)
s=re.sub(r'versão 3\.8\.[01]', 'versão 3.9.0', s, flags=re.I)
s=re.sub(r'versão antiga será removida e substituída pelo pacote completo atual', 'versão antiga será removida e substituída pelo pacote completo 3.9.0', s, flags=re.I)
welcome="""WizardForm.WelcomeLabel2.Caption :=
    'Instalador completo — funciona também em computadores que nunca tiveram o CSM Visualizador XML.' + #13#10 + #13#10 +
    'NOVIDADES DA VERSÃO 3.9.0' + #13#10 +
    '• NOVO: Entender a Tributação — explica e confere os impostos diretamente do XML' + #13#10 +
    '• Explicação simples para cliente e detalhamento técnico para a contabilidade' + #13#10 +
    '• Conferência de ICMS, redução, MVA/IVA-ST, ICMS-ST, IPI, FCP, DIFAL, PIS e COFINS' + #13#10 +
    '• Tratamento específico por CST/CSOSN, inclusive ICMS 60 e CSOSN 500 retidos anteriormente' + #13#10 +
    '• Resumo da NF-e e comparação automática com ICMSTot' + #13#10 +
    '• Relatório explicativo para copiar, imprimir ou salvar em PDF' + #13#10 + #13#10 +
    'MANTÉM TUDO DA VERSÃO ANTERIOR' + #13#10 +
    '• Motor Fiscal de Devolução total/parcial e referência por item' + #13#10 +
    '• Abertura de vários XMLs em abas na mesma janela' + #13#10 +
    '• Localizador Fiscal e Consulta DANFE' + #13#10 +
    '• Tema claro/escuro, Aba XML avançada e associação .xml' + #13#10 +
    '• Instalação limpa, atalho na Área de Trabalho e desinstalador' + #13#10 + #13#10 +
    'O instalador removerá versões antigas antes de instalar a 3.9.0.';"""
s,n=re.subn(r"WizardForm\.WelcomeLabel2\.Caption\s*:=.*?;\n\s*WizardForm\.WelcomeLabel2\.Font\.Color",welcome+'\n  WizardForm.WelcomeLabel2.Font.Color',s,flags=re.S)
if n!=1:raise SystemExit(f'Não consegui atualizar novidades do instalador: {n}')
s=re.sub(r"WizardForm\.FinishedLabel\.Caption := 'CSM Visualizador XML 3\.8\.[01] instalado com sucesso\.';","WizardForm.FinishedLabel.Caption := 'CSM Visualizador XML 3.9.0 instalado com sucesso.';",s)
for old,new in [('Tudo pronto para instalar a versão 3.8.0','Tudo pronto para instalar a versão 3.9.0'),('Tudo pronto para instalar a versão 3.8.1','Tudo pronto para instalar a versão 3.9.0'),('Instalando CSM Visualizador XML 3.8.0','Instalando CSM Visualizador XML 3.9.0'),('Instalando CSM Visualizador XML 3.8.1','Instalando CSM Visualizador XML 3.9.0'),('A versão 3.8.0 foi instalada','A versão 3.9.0 foi instalada'),('A versão 3.8.1 foi instalada','A versão 3.9.0 foi instalada'),('Abrir CSM Visualizador XML 3.8.0','Abrir CSM Visualizador XML 3.9.0'),('Abrir CSM Visualizador XML 3.8.1','Abrir CSM Visualizador XML 3.9.0')]:s=s.replace(old,new)
for token in ('#define AppVersion "3.9.0"','OutputBaseFilename=CSMVisualizadorXML-3.9.0-Instalador-Completo','VersionInfoVersion=3.9.0.0','PrivilegesRequired=lowest','Entender a Tributação','Motor Fiscal de Devolução','BrazilianPortuguese.isl'):
    if token not in s:raise SystemExit('Instalador 3.9.0 incompleto: '+token)
if 'PrivilegesRequired=admin' in s:raise SystemExit('Instalador ainda exige administrador')
p.write_text(s,encoding='utf-8',newline='\n')
print('ISS preparado para CSM Visualizador XML 3.9.0 com Entender a Tributação.')
