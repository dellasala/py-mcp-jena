# MCP Jena Connector

A Python-based HTTP service exposing Apache Jena Fuseki/SPARQL operations as tools for ADK multi-agent systems.

## Overview

This repository contains two entrypoints:

- ``:

  - Defines a FastMCP instance
  - Registers SPARQL tools (`execute_sparql_query`, `execute_sparql_update`, `list_graphs`, `sparql_query_templates`)
  - Reads configuration from environment variables:
    - `FUSEKI_URL` (default: `http://localhost:3030`)
    - `DEFAULT_DATASET` (default: `ontoFD`)
    - Optional `JENA_USERNAME` and `JENA_PASSWORD` for authenticated endpoints
  - Usage:
    ```bash
    python server.py               # starts on http://localhost:8000 using streaming HTTP
    python server.py --stateless   # run in stateless mode (no session state)
    ```

- ``:

  - Lightweight launcher that imports `mcp` from `server.py`
  - Builds an ASGI app via `mcp.streamable_http_app()`
  - Runs with **uvicorn**, allowing custom bind address and port
  - CLI options:
    - `--host` (default: `127.0.0.1`)
    - `--port` (default: `8000`)
    - `--stateless` to enable stateless HTTP
  - Usage examples:
    ```bash
    python server_http.py                 # bind 127.0.0.1:8000
    python server_http.py --port 9000     # use port 9000
    python server_http.py --host 0.0.0.0   # listen on all interfaces
    python server_http.py --stateless
    ```

## Getting Started

1. **Clone** this repo and navigate into it:

   ```bash
   git clone 
   cd mcp-server
   ```

2. **Create a virtual environment** and install dependencies:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Configure environment variables** (optional):

   ```bash
   export FUSEKI_URL=http://localhost:3030
   export DEFAULT_DATASET=ontoFD
   export JENA_USERNAME=<user>
   export JENA_PASSWORD=<pass>
   ```

4. **Run the server**:

   - Streaming HTTP (FastMCP):

     ```bash
     python server.py
     ```

   - Uvicorn launcher:

     ```bash
     python server_http.py --host 0.0.0.0 --port 8000
     ```

## Example: Using with google-adk

```python
from google_adk import MCPToolset
from google_adk.connection import StreamableHTTPConnectionParams

# Point to your running MCP server
SERVER_URL = "http://localhost:8000"

tool = MCPToolset(
    connection_params=StreamableHTTPConnectionParams(url=SERVER_URL)
)

# Now your ADK agents can call
result = tool.execute_sparql_query(query="SELECT ?s WHERE { ?s ?p ?o } LIMIT 1")
print(result)
```

This setup allows your ADK multi-agent system to use the MCP Jena Connector as a drop-in tool for SPARQL queries and updates.

