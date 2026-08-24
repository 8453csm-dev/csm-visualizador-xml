from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator
import sqlite3

from .xml_parser import FiscalDocument

SCHEMA = '''
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA temp_store=MEMORY;
CREATE TABLE IF NOT EXISTS documents (
  id INTEGER PRIMARY KEY,
  path TEXT NOT NULL UNIQUE,
  sha256 TEXT NOT NULL,
  size INTEGER NOT NULL,
  mtime_ns INTEGER NOT NULL,
  doc_type TEXT,
  model TEXT,
  access_key TEXT,
  number TEXT,
  series TEXT,
  issue_date TEXT,
  emitter_cnpj TEXT,
  emitter_name TEXT,
  recipient_cnpj TEXT,
  recipient_name TEXT,
  total_value TEXT,
  bc_icms TEXT,
  icms TEXT,
  icms_st TEXT,
  ipi TEXT,
  pis TEXT,
  cofins TEXT,
  status_code TEXT,
  status_text TEXT,
  indexed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_documents_key ON documents(access_key);
CREATE INDEX IF NOT EXISTS ix_documents_number ON documents(number);
CREATE INDEX IF NOT EXISTS ix_documents_emit ON documents(emitter_cnpj);
CREATE INDEX IF NOT EXISTS ix_documents_issue ON documents(issue_date);
CREATE TABLE IF NOT EXISTS items (
  id INTEGER PRIMARY KEY,
  document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  n_item INTEGER,
  code TEXT,
  description TEXT,
  ncm TEXT,
  cfop TEXT,
  cst TEXT,
  csosn TEXT,
  qty TEXT,
  unit_value TEXT,
  product_value TEXT,
  bc_icms TEXT,
  aliquot_icms TEXT,
  icms TEXT,
  ipi TEXT,
  pis TEXT,
  cofins TEXT
);
CREATE INDEX IF NOT EXISTS ix_items_ncm ON items(ncm);
CREATE INDEX IF NOT EXISTS ix_items_cfop ON items(cfop);
CREATE INDEX IF NOT EXISTS ix_items_description ON items(description);
'''


class LibraryDB:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as con:
            con.executescript(SCHEMA)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        con = sqlite3.connect(self.path, timeout=30)
        con.row_factory = sqlite3.Row
        con.execute('PRAGMA foreign_keys=ON')
        try:
            yield con
            con.commit()
        finally:
            con.close()

    def fingerprints(self) -> dict[str, tuple[int, int]]:
        with self.connect() as con:
            return {str(r['path']): (int(r['size']), int(r['mtime_ns'])) for r in con.execute('SELECT path,size,mtime_ns FROM documents')}

    def _upsert_on_connection(self, con: sqlite3.Connection, doc: FiscalDocument) -> int:
        con.execute('''
          INSERT INTO documents(path,sha256,size,mtime_ns,doc_type,model,access_key,number,series,issue_date,
            emitter_cnpj,emitter_name,recipient_cnpj,recipient_name,total_value,bc_icms,icms,icms_st,ipi,pis,cofins,status_code,status_text)
          VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
          ON CONFLICT(path) DO UPDATE SET
            sha256=excluded.sha256,size=excluded.size,mtime_ns=excluded.mtime_ns,doc_type=excluded.doc_type,model=excluded.model,
            access_key=excluded.access_key,number=excluded.number,series=excluded.series,issue_date=excluded.issue_date,
            emitter_cnpj=excluded.emitter_cnpj,emitter_name=excluded.emitter_name,recipient_cnpj=excluded.recipient_cnpj,
            recipient_name=excluded.recipient_name,total_value=excluded.total_value,bc_icms=excluded.bc_icms,icms=excluded.icms,
            icms_st=excluded.icms_st,ipi=excluded.ipi,pis=excluded.pis,cofins=excluded.cofins,status_code=excluded.status_code,
            status_text=excluded.status_text,indexed_at=CURRENT_TIMESTAMP
        ''', (
            doc.path, doc.sha256, doc.size, doc.mtime_ns, doc.doc_type, doc.model, doc.key, doc.number, doc.series, doc.issue_date,
            doc.emitter_cnpj, doc.emitter_name, doc.recipient_cnpj, doc.recipient_name, str(doc.total_value), str(doc.bc_icms),
            str(doc.icms), str(doc.icms_st), str(doc.ipi), str(doc.pis), str(doc.cofins), doc.status_code, doc.status_text
        ))
        row = con.execute('SELECT id FROM documents WHERE path=?', (doc.path,)).fetchone()
        doc_id = int(row['id'])
        con.execute('DELETE FROM items WHERE document_id=?', (doc_id,))
        if doc.items:
            con.executemany('''
              INSERT INTO items(document_id,n_item,code,description,ncm,cfop,cst,csosn,qty,unit_value,product_value,bc_icms,aliquot_icms,icms,ipi,pis,cofins)
              VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ''', [(
                doc_id, x.n_item, x.code, x.description, x.ncm, x.cfop, x.cst, x.csosn, str(x.qty), str(x.unit_value),
                str(x.product_value), str(x.bc_icms), str(x.aliquot_icms), str(x.icms), str(x.ipi), str(x.pis), str(x.cofins)
            ) for x in doc.items])
        return doc_id

    @contextmanager
    def writer(self):
        with self.connect() as con:
            yield lambda doc: self._upsert_on_connection(con, doc)

    def recent(self, limit: int = 300) -> list[dict]:
        with self.connect() as con:
            rows = con.execute('SELECT * FROM documents ORDER BY issue_date DESC, number DESC LIMIT ?', (limit,)).fetchall()
            return [dict(r) for r in rows]

    def search(self, query: str, limit: int = 100) -> list[dict]:
        q = f'%{query.strip()}%'
        with self.connect() as con:
            rows = con.execute('''
              SELECT DISTINCT d.* FROM documents d
              LEFT JOIN items i ON i.document_id=d.id
              WHERE d.access_key LIKE ? OR d.number LIKE ? OR d.emitter_cnpj LIKE ? OR d.emitter_name LIKE ?
                 OR d.recipient_cnpj LIKE ? OR d.recipient_name LIKE ? OR i.description LIKE ? OR i.ncm LIKE ? OR i.cfop LIKE ?
              ORDER BY d.issue_date DESC, d.number DESC LIMIT ?
            ''', (q,q,q,q,q,q,q,q,q,limit)).fetchall()
            return [dict(r) for r in rows]
