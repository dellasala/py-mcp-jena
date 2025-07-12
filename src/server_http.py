from __future__ import annotations

"""MCP Jena Connector – Streamable‑HTTP launcher


---------------------------------
* Import the `mcp` object from `server` (same tool namespace).
* Creates the ASGI app with `mcp.streamable_http_app()`.
* Runs **uvicorn** with customisable host/port (default 127.0.0.1:9000).
* Supports `--stateless` to enable stateless mode.

Examples:
```bash
python server_http.py                 # 127.0.0.1:9000
python server_http.py --port 7000     # porta diversa
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
    parser.add_argument("--port", type=int, default=9000, help="TCP port, default 8000")
    parser.add_argument("--stateless", action="store_true", help="Run in stateless mode (no sessions)")
    args = parser.parse_args()

    if args.stateless:
        mcp.settings.stateless_http = True

    app = mcp.streamable_http_app()
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
