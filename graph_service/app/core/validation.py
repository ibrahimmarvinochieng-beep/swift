"""Input validation for graph operations."""

import re
from fastapi import HTTPException, Path, Query

SAFE_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_:\-\.]+$")


def validate_node_id(v: str) -> str:
    """Validate node ID for Cypher injection prevention."""
    if not v or len(v) > 128:
        raise HTTPException(status_code=400, detail="Invalid node id length")
    if not SAFE_ID_PATTERN.match(v.strip()):
        raise HTTPException(
            status_code=400,
            detail="id must contain only alphanumeric, underscore, colon, hyphen, dot",
        )
    return v.strip()


def validate_safe_string(v: str, max_len: int = 255) -> str:
    """Validate string for injection (name, region, industry)."""
    if not v or len(v) > max_len:
        raise HTTPException(status_code=400, detail=f"Invalid string length (max {max_len})")
    # Reject obvious injection patterns
    if any(c in v for c in ["'", '"', "\\", ";", "{", "}", "(", ")"]):
        raise HTTPException(status_code=400, detail="Invalid characters in string")
    return v.strip()
