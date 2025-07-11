from __future__ import annotations

"""MCP Jena Connector – Streamable‑HTTP launcher

Questo file avvia il server FastMCP su un host/porta configurabili
attraverso CLI, evitando conflitti (WinError 10048) quando la porta
predefinita 8000 è già occupata.

Differenze rispetto a *server.py*
---------------------------------
* Importa l’oggetto `mcp` da `server` (stesso namespace dei tool).
* Crea l’ASGI app con `mcp.streamable_http_app()`.
* Esegue **uvicorn** con host/port personalizzabili (default 127.0.0.1:8000).
* Supporta `--stateless` per abilitare modalità stateless.

Esempi:
```bash
python server_http.py                 # 127.0.0.1:8000
python server_http.py --port 9000     # porta diversa
python server_http.py --host 0.0.0.0  # bind su tutte le interfacce
python server_http.py --stateless --port 7000
```
"""

import argparse
import uvicorn
from server import mcp  # importa il FastMCP definito in server.py


def main() -> None:
    parser = argparse.ArgumentParser(description="Run MCP Jena Connector (streamable-http)")
    parser.add_argument("--host", default="127.0.0.1", help="Bind address, default 127.0.0.1")
    parser.add_argument("--port", type=int, default=8000, help="TCP port, default 8000")
    parser.add_argument("--stateless", action="store_true", help="Run in stateless mode (no sessions)")
    args = parser.parse_args()

    if args.stateless:
        mcp.settings.stateless_http = True

    app = mcp.streamable_http_app()
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
