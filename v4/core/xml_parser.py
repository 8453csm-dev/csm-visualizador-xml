from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from defusedxml import ElementTree as ET
import hashlib


def _local(tag: str) -> str:
    return tag.rsplit('}', 1)[-1]


def _txt(parent, name: str, default: str = '') -> str:
    if parent is None:
        return default
    for el in parent.iter():
        if _local(el.tag) == name:
            return (el.text or '').strip()
    return default


def _child(parent, name: str):
    if parent is None:
        return None
    for el in parent.iter():
        if _local(el.tag) == name:
            return el
    return None


def _dec(value: str) -> Decimal:
    try:
        return Decimal((value or '0').replace(',', '.'))
    except (InvalidOperation, ValueError):
        return Decimal('0')


@dataclass(slots=True)
class FiscalItem:
    n_item: int = 0
    code: str = ''
    description: str = ''
    ncm: str = ''
    cfop: str = ''
    cst: str = ''
    csosn: str = ''
    qty: Decimal = Decimal('0')
    unit_value: Decimal = Decimal('0')
    product_value: Decimal = Decimal('0')
    bc_icms: Decimal = Decimal('0')
    aliquot_icms: Decimal = Decimal('0')
    icms: Decimal = Decimal('0')
    ipi: Decimal = Decimal('0')
    pis: Decimal = Decimal('0')
    cofins: Decimal = Decimal('0')


@dataclass(slots=True)
class FiscalDocument:
    path: str
    sha256: str
    size: int
    mtime_ns: int
    doc_type: str = 'XML'
    model: str = ''
    key: str = ''
    number: str = ''
    series: str = ''
    issue_date: str = ''
    emitter_cnpj: str = ''
    emitter_name: str = ''
    recipient_cnpj: str = ''
    recipient_name: str = ''
    total_value: Decimal = Decimal('0')
    bc_icms: Decimal = Decimal('0')
    icms: Decimal = Decimal('0')
    icms_st: Decimal = Decimal('0')
    ipi: Decimal = Decimal('0')
    pis: Decimal = Decimal('0')
    cofins: Decimal = Decimal('0')
    status_code: str = ''
    status_text: str = ''
    items: list[FiscalItem] = field(default_factory=list)


def _detect_type(root) -> tuple[str, str]:
    names = {_local(el.tag) for el in root.iter()}
    if 'infNFe' in names:
        return 'NF-e', _txt(root, 'mod') or '55'
    if 'infCte' in names or 'infCTe' in names:
        return 'CT-e', _txt(root, 'mod') or '57'
    if 'infMDFe' in names:
        return 'MDF-e', _txt(root, 'mod') or '58'
    if 'infNFSe' in names or 'infNfse' in names or 'CompNfse' in names:
        return 'NFS-e', 'NFS-e'
    if 'procEventoNFe' in names or 'evento' in names:
        return 'Evento NF-e', 'evento'
    return 'XML', _txt(root, 'mod')


def _id_key(root) -> str:
    for name in ('infNFe', 'infCte', 'infCTe', 'infMDFe'):
        el = _child(root, name)
        if el is not None:
            raw = (el.attrib.get('Id') or el.attrib.get('id') or '').strip()
            digits = ''.join(c for c in raw if c.isdigit())
            if len(digits) >= 44:
                return digits[-44:]
    for name in ('chNFe', 'chCTe', 'chMDFe'):
        digits = ''.join(c for c in _txt(root, name) if c.isdigit())
        if len(digits) == 44:
            return digits
    return ''


def _party(root, tag_name: str) -> tuple[str, str]:
    party = _child(root, tag_name)
    if party is None:
        return '', ''
    return _txt(party, 'CNPJ') or _txt(party, 'CPF'), _txt(party, 'xNome') or _txt(party, 'RazaoSocial')


def _parse_nfe_items(root) -> list[FiscalItem]:
    out: list[FiscalItem] = []
    for det in root.iter():
        if _local(det.tag) != 'det':
            continue
        prod = _child(det, 'prod')
        imposto = _child(det, 'imposto')
        if prod is None:
            continue
        out.append(FiscalItem(
            n_item=int(det.attrib.get('nItem') or 0), code=_txt(prod, 'cProd'), description=_txt(prod, 'xProd'),
            ncm=_txt(prod, 'NCM'), cfop=_txt(prod, 'CFOP'), cst=_txt(imposto, 'CST'), csosn=_txt(imposto, 'CSOSN'),
            qty=_dec(_txt(prod, 'qCom')), unit_value=_dec(_txt(prod, 'vUnCom')), product_value=_dec(_txt(prod, 'vProd')),
            bc_icms=_dec(_txt(imposto, 'vBC')), aliquot_icms=_dec(_txt(imposto, 'pICMS')), icms=_dec(_txt(imposto, 'vICMS')),
            ipi=_dec(_txt(imposto, 'vIPI')), pis=_dec(_txt(imposto, 'vPIS')), cofins=_dec(_txt(imposto, 'vCOFINS')),
        ))
    return out


def parse_xml(path: str | Path) -> FiscalDocument:
    p = Path(path)
    raw = p.read_bytes()
    root = ET.fromstring(raw)
    stat = p.stat()
    doc_type, model = _detect_type(root)
    emit_cnpj, emit_name = _party(root, 'emit')
    dest_cnpj, dest_name = _party(root, 'dest')
    total = _child(root, 'ICMSTot') or _child(root, 'total')
    doc = FiscalDocument(
        path=str(p.resolve()), sha256=hashlib.sha256(raw).hexdigest(), size=stat.st_size, mtime_ns=stat.st_mtime_ns,
        doc_type=doc_type, model=model, key=_id_key(root),
        number=_txt(root, 'nNF') or _txt(root, 'nCT') or _txt(root, 'nMDF') or _txt(root, 'nNFSe'), series=_txt(root, 'serie'),
        issue_date=_txt(root, 'dhEmi') or _txt(root, 'dEmi') or _txt(root, 'dhGer'),
        emitter_cnpj=emit_cnpj, emitter_name=emit_name, recipient_cnpj=dest_cnpj, recipient_name=dest_name,
        total_value=_dec(_txt(total, 'vNF') or _txt(total, 'vTPrest') or _txt(total, 'vServ')),
        bc_icms=_dec(_txt(total, 'vBC')), icms=_dec(_txt(total, 'vICMS')), icms_st=_dec(_txt(total, 'vST') or _txt(total, 'vICMSST')),
        ipi=_dec(_txt(total, 'vIPI')), pis=_dec(_txt(total, 'vPIS')), cofins=_dec(_txt(total, 'vCOFINS')),
        status_code=_txt(root, 'cStat'), status_text=_txt(root, 'xMotivo'),
    )
    if doc_type == 'NF-e':
        doc.items = _parse_nfe_items(root)
    return doc
