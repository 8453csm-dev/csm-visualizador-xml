from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from threading import Event, Lock, Thread
from uuid import uuid4
import os
import sys

import webview

from core import FolderImporter, LibraryDB, merge_pdfs


class AppApi:
    def __init__(self):
        base = Path(os.environ.get('LOCALAPPDATA') or Path.home()) / 'CSM Visualizador XML 4'
        base.mkdir(parents=True, exist_ok=True)
        self.db = LibraryDB(base / 'library.sqlite3')
        self.importer = FolderImporter(self.db)
        self.window = None
        self._ops: dict[str, dict] = {}
        self._cancel: dict[str, Event] = {}
        self._lock = Lock()

    def _new_op(self, kind: str, title: str) -> str:
        op = uuid4().hex
        with self._lock:
            self._ops[op] = {'id': op, 'kind': kind, 'title': title, 'status': 'running', 'processed': 0, 'total': 0, 'message': 'Preparando...', 'current': '', 'error': ''}
            self._cancel[op] = Event()
        return op

    def _patch_op(self, op: str, **changes):
        with self._lock:
            if op in self._ops:
                self._ops[op].update(changes)

    def choose_folder(self):
        result = self.window.create_file_dialog(webview.FileDialog.FOLDER)
        return result[0] if result else None

    def start_import(self, folder: str):
        if not folder:
            return None
        op = self._new_op('import', 'Importando pasta de XML')
        cancel = self._cancel[op]
        def work():
            try:
                def cb(p):
                    self._patch_op(op, processed=p.processed, total=p.total, message=p.message, current=p.current, imported=p.imported, cached=p.cached, failed=p.failed)
                result = self.importer.import_folder(folder, cb, cancel)
                self._patch_op(op, status='cancelled' if cancel.is_set() else 'done', **asdict(result))
            except Exception as e:
                self._patch_op(op, status='error', error=str(e), message='Falha na importação')
        Thread(target=work, name='csm-import', daemon=True).start()
        return op

    def cancel_operation(self, op: str):
        with self._lock:
            ev = self._cancel.get(op)
        if ev:
            ev.set()
            return True
        return False

    def operation(self, op: str):
        with self._lock:
            return dict(self._ops.get(op) or {})

    def documents(self, query: str = ''):
        return self.db.search(query, 300) if query.strip() else self.db.recent(300)

    def read_xml(self, path: str):
        p = Path(path)
        if p.suffix.lower() != '.xml' or not p.is_file():
            raise ValueError('XML inválido ou não encontrado')
        if p.stat().st_size > 20 * 1024 * 1024:
            raise ValueError('XML acima do limite de visualização de 20 MB')
        return p.read_text(encoding='utf-8-sig', errors='replace')

    def choose_pdfs(self):
        result = self.window.create_file_dialog(webview.FileDialog.LOAD, allow_multiple=True, file_types=('Arquivos PDF (*.pdf)',))
        return list(result or [])

    def start_pdf_merge(self, files: list[str]):
        if not files:
            return None
        save = self.window.create_file_dialog(webview.FileDialog.SAVE, save_filename='CSM PDF Unico.pdf', file_types=('Arquivo PDF (*.pdf)',))
        if not save:
            return None
        output = Path(save[0])
        if output.suffix.lower() != '.pdf':
            output = output.with_suffix('.pdf')
        op = self._new_op('pdf', 'Gerando PDF único')
        cancel = self._cancel[op]
        def work():
            try:
                def cb(p): self._patch_op(op, processed=p.processed, total=p.total, message=p.message, current=p.current)
                out = merge_pdfs(files, output, cb, cancel)
                self._patch_op(op, status='done', output=str(out), message='PDF único concluído')
            except Exception as e:
                self._patch_op(op, status='cancelled' if cancel.is_set() else 'error', error=str(e), message=str(e))
        Thread(target=work, name='csm-pdf', daemon=True).start()
        return op


def run():
    api = AppApi()
    base = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
    ui = base / 'ui' / 'index.html'
    window = webview.create_window('CSM Visualizador XML 4.0 Alpha', str(ui), js_api=api, width=1480, height=900, min_size=(1100, 700), text_select=True)
    api.window = window
    webview.start(gui='edgechromium', debug=False, private_mode=False, storage_path=str(Path(os.environ.get('LOCALAPPDATA') or Path.home()) / 'CSM Visualizador XML 4' / 'WebView2'))


if __name__ == '__main__':
    run()
