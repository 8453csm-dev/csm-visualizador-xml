const fs=require('fs');const vm=require('vm');const {JSDOM}=require('jsdom');
const dom=new JSDOM('<!doctype html><html><body></body></html>');global.DOMParser=dom.window.DOMParser;global.Intl=Intl;
vm.runInThisContext(fs.readFileSync(process.env.CSM_TAX_CORE||__dirname+'/tax_engine_core.js','utf8'));
const xml=fs.readFileSync(__dirname+'/tax_test_fixture.xml','utf8');
const a=CSM_TAX_CORE.analyze(CSM_TAX_CORE.parse(xml));const D=CSM_TAX_CORE.dec;
const cents=x=>D.str(D.round(x,2),2);function eq(label,got,want){if(cents(got)!==want)throw new Error(`${label}: ${cents(got)} != ${want}`)}
if(a.number!=='640645'||a.items.length!==2)throw new Error('Fixture não foi lida corretamente');
const i1=a.items[0],i2=a.items[1];
for(const [lab,item,field,want] of [
 ['Martelete BC ICMS',i1,'vBC','222.59'],['Martelete ICMS',i1,'vICMS','40.07'],['Martelete BC-ST',i1,'vBCST','351.24'],['Martelete ICMS-ST',i1,'vICMSST','23.16'],
 ['Furadeira BC ICMS',i2,'vBC','61.43'],['Furadeira ICMS',i2,'vICMS','11.06'],['Furadeira BC-ST',i2,'vBCST','96.94'],['Furadeira ICMS-ST',i2,'vICMSST','6.39']])eq(lab,D.parse(item.icms.fields[field]),want);
let sum=k=>a.items.reduce((acc,it)=>D.add(acc,D.parse(it.icms.fields[k]||'0')),D.parse('0'));
eq('Total BC ICMS',sum('vBC'),'284.02');eq('Total ICMS',sum('vICMS'),'51.13');eq('Total BC-ST',sum('vBCST'),'448.18');eq('Total ICMS-ST',sum('vICMSST'),'29.55');
if(i1.overall.code==='verify'||i2.overall.code==='verify')throw new Error('Itens de referência não deveriam exigir revisão');
const stSteps=i1.steps.map(x=>x.label+' '+x.formula).join('\n');
for(const token of ['MVA/IVA-ST de 50.0000%','50.0000% de','Base após somar a MVA','Redução da base do ICMS-ST','ICMS presumido da ST','Dedução do ICMS próprio','ICMS-ST final'])if(!stSteps.includes(token))throw new Error('Explicação ST incompleta: '+token);
if(i1.legal.benefitCode!=='SP020120')throw new Error('cBenef não identificado');
const xml60=`<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe"><NFe><infNFe Id="NFe35260900000000000000550000000000000000000001"><ide><mod>55</mod><nNF>1</nNF><serie>1</serie></ide><emit><xNome>A</xNome></emit><dest><xNome>B</xNome></dest><det><nItem>1</nItem><prod><cProd>X</cProd><xProd>RETIDO</xProd><NCM>27101932</NCM><CFOP>5405</CFOP><qCom>1</qCom><uCom>UN</uCom><vUnCom>21.40</vUnCom><vProd>21.40</vProd></prod><imposto><ICMS><ICMS60><orig>0</orig><CST>60</CST><vBCSTRet>21.40</vBCSTRet><vICMSSubstituto>0.00</vICMSSubstituto><vICMSSTRet>0.00</vICMSSTRet></ICMS60></ICMS></imposto></det><total><ICMSTot><vProd>21.40</vProd><vBC>0</vBC><vICMS>0</vICMS><vBCST>0</vBCST><vST>0</vST><vNF>21.40</vNF></ICMSTot></total></infNFe></NFe></nfeProc>`;
const a60=CSM_TAX_CORE.analyze(CSM_TAX_CORE.parse(xml60)).items[0];if(a60.icms.group!=='ICMS60')throw new Error('CST60 não reconhecido');if(a60.steps.some(x=>x.label==='ICMS-ST final'))throw new Error('CST60 recalculou ST indevidamente');if(!a60.steps.some(x=>x.label==='ICMS-ST retido anteriormente'))throw new Error('CST60 não explicou retenção anterior');
console.log('OK - Entender a Tributação confere NF 640645, precisão ST e tratamento CST60.');
