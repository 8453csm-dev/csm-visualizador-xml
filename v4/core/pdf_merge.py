from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from threading import Event
from typing import Callable

from pypdf import PdfReader, PdfWriter


@dataclass(slots=True)
class PdfProgress:
    total: int
    processed: int = 0
    current: str = ''
    message: str = ''


def merge_pdfs(files: list[str | Path], output: str | Path, progress: Callable[[PdfProgress], None] | None = None, cancel: Event | None = None) -> Path:
    src = [Path(x) for x in files]
    state = PdfProgress(total=len(src), message='Preparando PDF único')
    if progress:
        progress(state)
    writer = PdfWriter()
    for idx, path in enumerate(src, 1):
        if cancel and cancel.is_set():
            raise RuntimeError('Geração de PDF cancelada')
        state.current = path.name
        reader = PdfReader(str(path))
        for page in reader.pages:
            writer.add_page(page)
        state.processed = idx
        state.message = f'Adicionando PDF {idx} de {state.total}'
        if progress:
            progress(state)
    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(out.suffix + '.part')
    with tmp.open('wb') as f:
        writer.write(f)
    tmp.replace(out)
    state.current = ''
    state.message = 'PDF único concluído'
    if progress:
        progress(state)
    return out
