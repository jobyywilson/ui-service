import os
from dataclasses import dataclass
from typing import Optional

from app.config import ConfigurationError


@dataclass(frozen=True)
class Neo4jSettings:
    uri: str
    username: str
    password: str
    database: Optional[str]
    verify_connectivity: bool


def get_neo4j_settings(environment=None):
    source = environment if environment is not None else os.environ
    required = ("NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD")
    missing = [name for name in required if not source.get(name)]
    if missing:
        raise ConfigurationError("Missing Neo4j settings: " + ", ".join(missing))
    uri = source["NEO4J_URI"]
    if not uri.startswith(("neo4j+s://", "neo4j+ssc://")):
        raise ConfigurationError(
            "NEO4J_URI must use encrypted neo4j+s:// for cloud"
        )
    verify = source.get("NEO4J_VERIFY_CONNECTIVITY", "true").lower()
    return Neo4jSettings(
        uri, source["NEO4J_USERNAME"], source["NEO4J_PASSWORD"],
        source.get("NEO4J_DATABASE") or None,
        verify in {"1", "true", "yes", "on"},
    )
