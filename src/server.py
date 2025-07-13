from __future__ import annotations

"""MCP Jena Connector – Python implementation (Streamable-HTTP) 

Avvio rapido (porta 9000):
-------------------------
```bash
python server.py              # starts at http://localhost:9000/mcp
python server.py --stateless   # stateless mode
```

Variabili ambiente per Jena/Fuseki:
```
FUSEKI_URL      # e.g. http://localhost:3030
DEFAULT_DATASET # e.g. ontoFD
JENA_USERNAME   # optional
JENA_PASSWORD   # optional
```
"""

import os
import argparse
from typing import Any, Dict, List

import httpx
from httpx import RequestError, HTTPStatusError
from pydantic import Field
from mcp.server.fastmcp import FastMCP


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
        self.dataset = (dataset or os.getenv("DEFAULT_DATASET", "ontoFD")).lstrip('/')
        self.auth = (
            username or os.getenv("JENA_USERNAME"),
            password or os.getenv("JENA_PASSWORD"),
        )
        if not any(self.auth):
            self.auth = None  # type: ignore
        self.timeout = timeout

    def execute_query(self, query: str) -> Dict[str, Any]:
        """Executes a SPARQL SELECT/ASK query and returns JSON result."""
        url = f"{self.base_url}/{self.dataset}/query"
        try:
            resp = httpx.get(
                url,
                params={"query": query},
                headers={"Accept": "application/sparql-results+json"},
                auth=self.auth,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return resp.json()
        except RequestError as err:
            raise SparqlError(f"Connection error during SPARQL query: {err}") from err
        except HTTPStatusError as err:
            text = err.response.text.strip() if err.response else "<no body>"
            raise SparqlError(f"SPARQL query failed ({err.response.status_code}): {text}") from err

    def execute_update(self, update: str) -> str:
        """Executes a SPARQL UPDATE and returns a confirmation message."""
        url = f"{self.base_url}/{self.dataset}/update"
        try:
            resp = httpx.post(
                url,
                data={"update": update},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                auth=self.auth,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return "Update successful"
        except RequestError as err:
            raise SparqlError(f"Connection error during SPARQL update: {err}") from err
        except HTTPStatusError as err:
            text = err.response.text.strip() if err.response else "<no body>"
            raise SparqlError(f"SPARQL update failed ({err.response.status_code}): {text}") from err

    def list_graphs(self) -> List[str]:
        """Lists distinct graph URIs in the dataset."""
        result = self.execute_query(
            "SELECT DISTINCT ?g WHERE { GRAPH ?g { ?s ?p ?o } } ORDER BY ?g"
        )
        return [b["g"]["value"] for b in result["results"]["bindings"]]


def _templates_for_category(cat: str) -> Dict[str, Any]:
    """Return SPARQL query templates grouped by category."""
    catalogue: Dict[str, List[str]] = {
        "select": [
            "SELECT ?s WHERE { ?s ?p ?o } LIMIT 10",
            "SELECT ?subject ?predicate ?object WHERE { ?subject ?predicate ?object }"
        ],
        "update": [
            "INSERT DATA { GRAPH <http://example.org> { <http://example.org/subject> <http://example.org/predicate> \"object\" } }",
            "DELETE WHERE { GRAPH <http://example.org> { ?s ?p ?o } }"
        ],
    }
    # 'all' category combines every template
    all_templates = []
    for templates in catalogue.values():
        all_templates.extend(templates)
    catalogue["all"] = all_templates
    # Return templates for requested category
    return {"category": cat, "templates": catalogue.get(cat, [])}


mcp = FastMCP("MCP Jena Connector", dependencies=["httpx"])

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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MCP Jena Connector (streamable-http)")
    parser.add_argument("--stateless", action="store_true", help="Run stateless HTTP (no session state)")
    args = parser.parse_args()

    if args.stateless:
        mcp.settings.stateless_http = True

    mcp.run(transport="streamable-http")
