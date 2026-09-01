from __future__ import annotations

import argparse
import json
import time
import urllib.request
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--timeout", type=float, default=30.0)
    args = ap.parse_args()

    out = Path(args.out)
    deadline = time.monotonic() + args.timeout
    req = urllib.request.Request(
        "http://127.0.0.1:47878/events",
        headers={"Accept": "text/event-stream"},
    )

    with urllib.request.urlopen(req, timeout=args.timeout) as resp:
        while time.monotonic() < deadline:
            raw = resp.readline()
            if not raw:
                time.sleep(0.05)
                continue
            line = raw.decode("utf-8", errors="replace").strip()
            if not line.startswith("data:"):
                continue
            payload = json.loads(line[5:].strip())
            path = str(payload.get("path") or "").strip()
            if not path:
                continue
            out.write_text(path, encoding="utf-8")
            data = json.dumps({"path": path}).encode("utf-8")
            ack = urllib.request.Request(
                "http://127.0.0.1:47878/ack",
                data=data,
                method="POST",
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(ack, timeout=5) as ack_resp:
                if not (200 <= ack_resp.status < 300):
                    raise RuntimeError(f"ACK falhou: HTTP {ack_resp.status}")
            return 0

    raise TimeoutError("Nenhum XML recebido pelo canal SSE")


if __name__ == "__main__":
    raise SystemExit(main())
