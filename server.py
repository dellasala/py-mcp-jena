from __future__ import annotations

"""MCP Jena Connector – Python implementation (Streamable-HTTP) 

Avvio rapido (porta 8000):
-------------------------
```bash
python server.py              # http://localhost:8000/mcp
python server.py --stateless   # stateless mode
```

Variabili ambiente per Jena/Fuseki:
```
FUSEKI_URL      # es. http://localhost:3030
DEFAULT_DATASET # es. ontoFD
JENA_USERNAME   # opzionale
JENA_PASSWORD   # opzionale
```
"""

###############################################################################
# Imports & setup                                                             #
###############################################################################

import os
import urllib.parse
import argparse
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP

###############################################################################
# Helper classes                                                              #
###############################################################################


class SparqlError(RuntimeError):
    """Raised when a SPARQL HTTP operation fails."""


class JenaClient:
    """Tiny helper around Apache Jena Fuseki HTTP API."""

    def __init__(
        self,
        base_url: str | None = None,
        dataset: str | None = None,
        username: str | None = None,
        password: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = (base_url or os.getenv("FUSEKI_URL", "http://localhost:3030")).rstrip('/')
        self.dataset  = (dataset or os.getenv("DEFAULT_DATASET", "ontoFD")).lstrip('/')
        self.auth = (
            username or os.getenv("JENA_USERNAME"),
            password or os.getenv("JENA_PASSWORD"),
        )
        if not any(self.auth):
            self.auth = None  # type: ignore  # httpx expects Tuple[str, str] | None
        self.timeout = timeout

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def execute_query(self, query: str) -> Dict[str, Any]:
        params = {"query": query}
        url = f"{self.base_url.rstrip('/')}/{self.dataset}/query"
        try:
            resp = httpx.get(
                url,
                params=params,
                headers={"Accept": "application/sparql-results+json"},
                auth=self.auth,  # type: ignore[arg-type]
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            raise SparqlError(self._err("query", exc)) from exc

    def execute_update(self, update: str) -> str:
        url = f"{self.base_url.rstrip('/')}/{self.dataset}/update"
        data = urllib.parse.urlencode({"update": update})
        try:
            resp = httpx.post(
                url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                auth=self.auth,  # type: ignore[arg-type]
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return "Update successful"
        except httpx.HTTPError as exc:
            raise SparqlError(self._err("update", exc)) from exc

    def list_graphs(self) -> List[str]:
        result = self.execute_query(
            "SELECT DISTINCT ?g WHERE { GRAPH ?g { ?s ?p ?o } } ORDER BY ?g"
        )
        return [b["g"]["value"] for b in result["results"]["bindings"]]

    @staticmethod
    def _err(kind: str, exc: httpx.HTTPError) -> str:
        if isinstance(exc, httpx.TimeoutException):
            return f"SPARQL {kind} timed-out: {exc!s}"
        if exc.response is not None:
            return f"SPARQL {kind} failed ({exc.response.status_code}): {exc.response.text.strip()}"
        return f"SPARQL {kind} failed: {exc!s}"

###############################################################################
# SPARQL template catalogue                                                   #
###############################################################################

template_catalogue: Dict[str, List[Dict[str, str]]] = {
    # (omesso per brevità – identico alla versione precedente)
}


def _templates_for_category(cat: str) -> Dict[str, Any]:
    if cat == "all":
        return template_catalogue
    if cat not in template_catalogue:
        raise ValueError(
            "Unknown category – use exploration, property-paths, statistics, validation, schema, all"
        )
    return {cat: template_catalogue[cat]}

###############################################################################
# FastMCP server definition                                                   #
###############################################################################

mcp = FastMCP("MCP Jena Connector", dependencies=["httpx"])

# ------------------------------------------------------------------
# Tools
# ------------------------------------------------------------------

@mcp.tool()
def execute_sparql_query(
    query: str = Field(..., description="SPARQL query to execute"),
    dataset: str | None = Field(None, description="Dataset name (override)"),
    endpoint: str | None = Field(None, description="Fuseki base URL (override)"),
) -> Dict[str, Any]:
    client = JenaClient(endpoint, dataset)
    return {"status": "success", "data": client.execute_query(query)}


@mcp.tool()
def execute_sparql_update(
    update: str = Field(..., description="SPARQL update to execute"),
    dataset: str | None = Field(None),
    endpoint: str | None = Field(None),
) -> Dict[str, str]:
    client = JenaClient(endpoint, dataset)
    return {"status": "success", "message": client.execute_update(update)}


@mcp.tool()
def list_graphs(
    dataset: str | None = Field(None),
    endpoint: str | None = Field(None),
) -> Dict[str, Any]:
    client = JenaClient(endpoint, dataset)
    return {"status": "success", "graphs": client.list_graphs()}


@mcp.tool()
def sparql_query_templates(
    category: str = Field("all", description="Template category")
) -> Dict[str, Any]:
    return {"status": "success", "templates": _templates_for_category(category)}

###############################################################################
# Entrypoint (streamable-http)                                                #
###############################################################################

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MCP Jena Connector (streamable-http)")
    parser.add_argument("--stateless", action="store_true", help="Run stateless HTTP (no session state)")
    args = parser.parse_args()

    if args.stateless:
        mcp.settings.stateless_http = True

    mcp.run(transport="streamable-http")