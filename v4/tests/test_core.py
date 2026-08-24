from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.db import LibraryDB
from core.importer import FolderImporter
from core.xml_parser import parse_xml

NFE = '''<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe"><NFe><infNFe Id="NFe35260812345678000123550010000001231234567890"><ide><mod>55</mod><serie>1</serie><nNF>123</nNF><dhEmi>2026-08-24T10:00:00-03:00</dhEmi></ide><emit><CNPJ>12345678000123</CNPJ><xNome>EMITENTE TESTE</xNome></emit><dest><CNPJ>98765432000198</CNPJ><xNome>DEST TESTE</xNome></dest><det nItem="1"><prod><cProd>A1</cProd><xProd>PRODUTO TESTE</xProd><NCM>94036000</NCM><CFOP>5102</CFOP><qCom>2</qCom><vUnCom>50</vUnCom><vProd>100</vProd></prod><imposto><ICMS><ICMS00><orig>0</orig><CST>00</CST><vBC>100</vBC><pICMS>18</pICMS><vICMS>18</vICMS></ICMS00></ICMS></imposto></det><total><ICMSTot><vBC>100</vBC><vICMS>18</vICMS><vNF>105</vNF></ICMSTot></total></infNFe></NFe><protNFe><infProt><cStat>100</cStat><xMotivo>Autorizado o uso da NF-e</xMotivo></infProt></protNFe></nfeProc>'''


def test_parse_nfe(tmp_path: Path):
    p = tmp_path / 'nfe.xml'
    p.write_text(NFE, encoding='utf-8')
    d = parse_xml(p)
    assert d.doc_type == 'NF-e'
    assert d.number == '123'
    assert d.key == '35260812345678000123550010000001231234567890'
    assert len(d.items) == 1
    assert d.items[0].cfop == '5102'


def test_import_cache_and_search(tmp_path: Path):
    folder = tmp_path / 'xmls'
    folder.mkdir()
    for i in range(12):
        (folder / f'{i}.xml').write_text(NFE.replace('<nNF>123</nNF>', f'<nNF>{1000+i}</nNF>').replace('PRODUTO TESTE', f'PRODUTO TESTE {i}'), encoding='utf-8')
    db = LibraryDB(tmp_path / 'library.sqlite3')
    imp = FolderImporter(db, workers=4)
    first = imp.import_folder(folder)
    second = imp.import_folder(folder)
    assert first.imported == 12 and first.failed == 0
    assert second.cached == 12 and second.imported == 0
    rows = db.search('PRODUTO TESTE 7')
    assert rows and rows[0]['number'] == '1007'
