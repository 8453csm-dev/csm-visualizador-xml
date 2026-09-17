from pathlib import Path
import sys

# Executa o patch 3.13.0 corrigindo somente a validação final do próprio script.
# O módulo original já contém a frase fiscal completa "Ciência da Operação (210210)";
# a revisão anterior exigia, por engano, o literal inexistente "Registrar Ciência".
orig = Path(__file__).with_name('patch_native_nfe_workflow_3130.py')
text = orig.read_text(encoding='utf-8')
old = "'Registrar Ciência'):"
new = "'Ciência da Operação (210210)'):"
if old not in text:
    raise SystemExit('Validação antiga do frontend 3.13.0 não encontrada')
text = text.replace(old, new, 1)
code = compile(text, str(orig), 'exec')
ns = {'__name__': '__main__', '__file__': str(orig)}
exec(code, ns, ns)
