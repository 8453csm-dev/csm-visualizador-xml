// CSM_DIFAL_ST_DISPLAY_3102
// Mantem a apuracao isolada por CFOP+aliquota internamente, mas exibe somente a aliquota ao usuario.
(() => {
  'use strict';

  function setText(el,value){if(el && el.textContent!==value)el.textContent=value}

  function cleanMainSummary(root=globalThis.document){
    if(!root)return;
    const view=root.querySelector?.('#difalstView');
    if(!view)return;

    const sectionTitle=view.querySelector('.csm-difal-section-title');
    if(sectionTitle){
      const strong=sectionTitle.querySelector('strong');
      const small=sectionTitle.querySelector('small');
      const badge=sectionTitle.querySelector(':scope > span');
      setText(strong,'Resumo por alíquota');
      setText(small,'Cada cálculo é apurado isoladamente; bases de operações diferentes não são misturadas.');
      if(badge){
        const m=(badge.textContent||'').match(/\d+/);
        if(m)setText(badge,`${m[0]} cálculo(s)`);
      }
    }

    view.querySelectorAll('.csm-difal-summary .csm-difal-card-title').forEach(title=>{
      const txt=(title.textContent||'').trim();
      const m=txt.match(/^CFOP\s+[^•]+\s*•\s*([0-9.,]+%)\s*•\s*(DIFAL|ICMS ST)$/i);
      if(m)setText(title,`Alíquota interestadual ${m[1]}`);
    });

    const note=view.querySelector('.csm-difal-note');
    if(note && /CFOP\s*\+\s*alíquota/i.test(note.textContent||'')){
      note.innerHTML='<b>Regra aplicada:</b> a tela apresenta o resultado por <b>alíquota interestadual</b>. Operações diferentes são calculadas isoladamente e suas bases não são misturadas no mesmo cálculo. Marque <b>Calcular como ICMS ST</b> quando a mercadoria estiver sujeita à substituição tributária.';
    }
  }

  function cleanFiscalSummary(root=globalThis.document){
    if(!root)return;
    const panel=root.querySelector?.('#csmDifalFiscalPanel');
    if(!panel)return;

    const headSmall=panel.querySelector('.csm-difal-fiscal-head small');
    setText(headSmall,'Apuração separada por alíquota interestadual');

    panel.querySelectorAll('.csm-difal-fiscal-row').forEach(row=>{
      const first=row.querySelector(':scope > span:first-child');
      if(!first)return;
      const b=first.querySelector('b');
      const small=first.querySelector('small');
      if(!b||!small)return;
      const parts=(small.textContent||'').split('•').map(x=>x.trim()).filter(Boolean);
      const rate=parts.find(x=>/%$/.test(x));
      if(/^CFOP\s+/i.test(b.textContent||'') && rate)setText(b,`Alíquota interestadual ${rate}`);
      if(parts.length && rate){
        const filtered=parts.filter(x=>x!==rate).join(' • ');
        setText(small,filtered);
      }
    });
  }

  let scheduled=false;
  function apply(){scheduled=false;cleanMainSummary();cleanFiscalSummary()}
  function schedule(){if(scheduled)return;scheduled=true;Promise.resolve().then(apply)}
  const root=globalThis.document?.body||globalThis.document?.documentElement;
  if(root){
    const obs=new MutationObserver(schedule);
    obs.observe(root,{childList:true,subtree:true,characterData:true});
  }
  schedule();
  globalThis.CSM_DIFAL_ST_DISPLAY_3102={apply,schedule};
})();
