const fs=require('fs');
const p='installer-v2/devolution_engine_v2_patch.js';
const s=fs.readFileSync(p,'utf8');
const required=[
 'CSM_DEVOLUTION_ENGINE_V2',
 'Devolução da NF',
 'Todos os ${draft.lines.length} itens da NF-e estão incluídos automaticamente',
 'data-dev-bulk="visible"',
 'Selecionar todos',
 'DADOS DA NF-e DE DEVOLUÇÃO',
 'CÁLCULO DO IMPOSTO',
 'TRANSPORTADOR / VOLUMES TRANSPORTADOS',
 'DADOS DOS PRODUTOS / SERVIÇOS',
 'Conferência interna do fiscal',
 'não aparece no PDF do cliente',
 'Nota Técnica NF-e 2025.002',
 'document.title=newTitle'
];
for(const x of required)if(!s.includes(x))throw new Error('Beta 2 ausente: '+x);
const guide=s.slice(s.indexOf('function csmDevGuideHtml'),s.indexOf('function csmDevDownloadGuide'));
if(guide.includes('Alertas para revisão'))throw new Error('PDF Beta 2 ainda contém Alertas para revisão');
if(guide.includes('&lt;DFeReferenciado&gt;'))throw new Error('PDF Beta 2 ainda expõe bloco XML técnico ao cliente');
console.log('Motor Fiscal Beta 2: UX/PDF OK');
