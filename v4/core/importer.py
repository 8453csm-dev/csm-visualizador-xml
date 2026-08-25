from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from threading import Event
from typing import Callable
import os

from .db import LibraryDB
from .xml_parser import FiscalDocument, parse_xml


@dataclass(slots=True)
class ImportProgress:
    total: int
    processed: int = 0
    imported: int = 0
    cached: int = 0
    failed: int = 0
    current: str = ''
    message: str = ''

ProgressCallback = Callable[[ImportProgress], None]


class FolderImporter:
    def __init__(self, db: LibraryDB, workers: int | None = None):
        self.db = db
        cpu = os.cpu_count() or 4
        self.workers = workers or min(max(cpu, 4), 12)

    def discover(self, folder: str | Path) -> list[Path]:
        root = Path(folder)
        return sorted(p for p in root.rglob('*') if p.is_file() and p.suffix.lower() == '.xml')

    def import_folder(self, folder: str | Path, progress: ProgressCallback | None = None, cancel: Event | None = None) -> ImportProgress:
        files = self.discover(folder)
        state = ImportProgress(total=len(files), message='Preparando importação')
        if progress:
            progress(state)
        changed: list[Path] = []
        fingerprints = self.db.fingerprints()
        for p in files:
            if cancel and cancel.is_set():
                state.message = 'Cancelado'
                return state
            st = p.stat()
            fp = fingerprints.get(str(p.resolve()))
            if fp == (st.st_size, st.st_mtime_ns):
                state.cached += 1
                state.processed += 1
            else:
                changed.append(p)
        if progress:
            state.message = f'{state.cached} XMLs já indexados; {len(changed)} para processar'
            progress(state)

        def parse_one(p: Path) -> tuple[Path, FiscalDocument | None, Exception | None]:
            try:
                return p, parse_xml(p), None
            except Exception as e:
                return p, None, e

        with self.db.writer() as write_doc:
            with ThreadPoolExecutor(max_workers=self.workers, thread_name_prefix='csm-xml') as pool:
                futures = [pool.submit(parse_one, p) for p in changed]
                for fut in as_completed(futures):
                    if cancel and cancel.is_set():
                        for f in futures:
                            f.cancel()
                        state.message = 'Cancelado'
                        break
                    p, doc, err = fut.result()
                    state.current = p.name
                    if err is None and doc is not None:
                        write_doc(doc)
                        state.imported += 1
                    else:
                        state.failed += 1
                    state.processed += 1
                    state.message = f'Processando {state.processed} de {state.total} XMLs'
                    if progress:
                        progress(state)
        if not (cancel and cancel.is_set()):
            state.message = 'Importação concluída'
            state.current = ''
            if progress:
                progress(state)
        return state
