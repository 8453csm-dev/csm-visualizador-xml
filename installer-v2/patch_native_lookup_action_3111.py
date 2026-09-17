from pathlib import Path

p=Path('installer-v2/native_lookup_module.js')
s=p.read_text(encoding='utf-8')
marker='CSM_NATIVE_LOOKUP_ACTION_3111'
if marker in s:
    print('Hotfix 3.11.1 ja aplicado ao modulo nativo')
    raise SystemExit(0)
old="""function findActionButton(input){
  let root=input.parentElement;
  for(let depth=0;root&&depth<7;depth++,root=root.parentElement){
    const buttons=[...root.querySelectorAll('button,[role=\"button\"],a')].filter(el=>!isOwnNativeControl(el));
    const hit=buttons.find(el=>{const t=normText(textOf(el));return /consultar|localizar|buscar|baixar/.test(t)&&!/historico|limpar/.test(t)});
    if(hit)return {button:hit,root};
  }
  return {button:null,root:input.parentElement||document};
}
"""
new="""// CSM_NATIVE_LOOKUP_ACTION_3111
function actionHay(el){
  return normText([textOf(el),el?.id,el?.name,el?.className,el?.title,el?.getAttribute?.('aria-label'),el?.getAttribute?.('data-action'),el?.getAttribute?.('type')].filter(Boolean).join(' '));
}
function actionScore(el,input,depth){
  if(!el||isOwnNativeControl(el)||!visible(el)||el.disabled)return -9999;
  const h=actionHay(el);let score=0;
  if(el.tagName==='BUTTON')score+=8;
  if(String(el.getAttribute?.('type')||'').toLowerCase()==='submit')score+=35;
  if(/consultar|consulta|localizar|buscar|pesquisar|procurar|continuar|acessar|abrir|visualizar|gerar|danfe|xml|nfe|nf-e/.test(h))score+=28;
  if(/primary|principal|confirm|submit|search|lookup|go|play/.test(h))score+=12;
  if(/fechar|cancelar|limpar|historico|histórico|voltar|copiar|config|ajuda|sair/.test(h))score-=80;
  if(input?.form&&el.form===input.form)score+=45;
  try{
    const a=input.getBoundingClientRect(),b=el.getBoundingClientRect();
    const dy=Math.abs((a.top+a.bottom)/2-(b.top+b.bottom)/2),dx=Math.abs((a.left+a.right)/2-(b.left+b.right)/2);
    if(dy<90)score+=25;else if(dy<220)score+=10;
    if(dx<700)score+=8;
  }catch(_){}
  score+=Math.max(0,14-depth*2);
  return score;
}
function findActionButton(input){
  const selector='button,input[type=\"submit\"],input[type=\"button\"],[role=\"button\"],a,[data-action]';
  let root=input.parentElement,best=null,bestScore=-9999,bestRoot=root;
  for(let depth=0;root&&depth<9;depth++,root=root.parentElement){
    for(const el of root.querySelectorAll(selector)){
      const score=actionScore(el,input,depth);
      if(score>bestScore){best={button:el,root};bestScore=score;bestRoot=root}
    }
    if(bestScore>=55)break;
  }
  if(!best||bestScore<18)return {button:null,root:bestRoot||input.parentElement||document,score:bestScore};
  return {...best,score:bestScore};
}
function submitLookup(input,button){
  if(button){button.click();return 'button'}
  const form=input?.form||input?.closest?.('form');
  if(form){
    try{if(typeof form.requestSubmit==='function'){form.requestSubmit();return 'form'}}catch(_){}
    try{form.dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}));return 'form-event'}catch(_){}
  }
  const opts={key:'Enter',code:'Enter',keyCode:13,which:13,bubbles:true,cancelable:true};
  input.dispatchEvent(new KeyboardEvent('keydown',opts));
  input.dispatchEvent(new KeyboardEvent('keypress',opts));
  input.dispatchEvent(new KeyboardEvent('keyup',opts));
  return 'enter';
}
"""
if old not in s:
    raise SystemExit('Bloco findActionButton da 3.11.0 nao encontrado')
s=s.replace(old,new,1)
old_dispatch="""  const {button,root}=findActionButton(input);
  if(!button)throw new Error('Localizador encontrado, mas o botão de consulta não foi identificado.');
  setProviderAndFormat(root||document);
  setNativeValue(input,key);
  input.focus();
  setStatus('Chave validada. Consultando a NF-e…','work');
  button.click();
  saveHistory(key);
  return true;
"""
new_dispatch="""  const {button,root}=findActionButton(input);
  setProviderAndFormat(root||input.form||document);
  setNativeValue(input,key);
  input.focus();
  setStatus('Chave validada. Consultando a NF-e…','work');
  const method=submitLookup(input,button);
  console.info('CSM Consulta NF-e 3.11.1: acionamento',method);
  saveHistory(key);
  return true;
"""
if old_dispatch not in s:
    raise SystemExit('Bloco dispatchLookup da 3.11.0 nao encontrado')
s=s.replace(old_dispatch,new_dispatch,1)
p.write_text(s,encoding='utf-8',newline='\n')
print('Hotfix 3.11.1 aplicado: acao por score + submit + Enter')
