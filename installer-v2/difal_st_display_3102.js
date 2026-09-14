// CSM_DIFAL_ST_DISPLAY_3102
// Mantem a apuracao isolada por CFOP+aliquota internamente, mas exibe somente a aliquota ao usuario.
(() => {
  'use strict';

  function cleanMainSummary(root=document){
    const view=root.querySelector?.('#difalstView');
    if(!view)return;

    const sectionTitle=view.querySelector('.csm-difal-section-title');
    if(sectionTitle){
      const strong=sectionTitle.querySelector('strong');
      const small=sectionTitle.querySelector('small');
      const badge=sectionTitle.querySelector(':scope > span');
      if(strong)strong.textContent='Resumo por alíquota';
      if(small)small.textContent='Cada cálculo é apurado isoladamente; bases de operações diferentes não são misturadas.';
      if(badge){
        const m=(badge.textContent||'').match(/\d+/);
        if(m)badge.textContent=`${m[0]} cálculo(s)`;
      }
    }

    view.querySelectorAll('.csm-difal-summary .csm-difal-card-title').forEach(title=>{
      const txt=(title.textContent||'').trim();
      const m=txt.match(/^CFOP\s+[^•]+\s*•\s*([0-9.,]+%)\s*•\s*(DIFAL|ICMS ST)$/i);
      if(m)title.textContent=`Alíquota interestadual ${m[1]}`;
    });

    const note=view.querySelector('.csm-difal-note');
    if(note && /CFOP\s*\+\s*alíquota/i.test(note.textContent||'')){
      note.innerHTML='<b>Regra aplicada:</b> a tela apresenta o resultado por <b>alíquota interestadual</b>. Operações diferentes são calculadas isoladamente e suas bases não são misturadas no mesmo cálculo. Marque <b>Calcular como ICMS ST</b> quando a mercadoria estiver sujeita à substituição tributária.';
    }
  }

  function cleanFiscalSummary(root=document){
    const panel=root.querySelector?.('#csmDifalFiscalPanel');
    if(!panel)return;

    const headSmall=panel.querySelector('.csm-difal-fiscal-head small');
    if(headSmall)headSmall.textContent='Apuração separada por alíquota interestadual';

    panel.querySelectorAll('.csm-difal-fiscal-row').forEach(row=>{
      const first=row.querySelector(':scope > span:first-child');
      if(!first)return;
      const b=first.querySelector('b');
      const small=first.querySelector('small');
      if(!b||!small)return;
      const parts=(small.textContent||'').split('•').map(x=>x.trim()).filter(Boolean);
      const rate=parts.find(x=>/%$/.test(x));
      if(/^CFOP\s+/i.test(b.textContent||'') && rate)b.textContent=`Alíquota interestadual ${rate}`;
      if(parts.length){
        const filtered=parts.filter(x=>x!==rate);
        small.textContent=filtered.join(' • ');
      }
    });
  }

  function apply(){cleanMainSummary();cleanFiscalSummary()}
  const root=document.body||document.documentElement;
  if(root){
    const obs=new MutationObserver(()=>apply());
    obs.observe(root,{childList:true,subtree:true});
  }
  Promise.resolve().then(apply);
  globalThis.CSM_DIFAL_ST_DISPLAY_3102={apply};
})();
