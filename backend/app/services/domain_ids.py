from __future__ import annotations

import re
from pathlib import Path

SAFE_DOMAIN_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")
SAFE_SYSTEM_ID_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


def safe_domain_dir(domains_root: Path, domain_id: str) -> Path:
    if not SAFE_DOMAIN_ID_RE.fullmatch(domain_id):
        raise KeyError(f"Unknown domain_id {domain_id!r}")
    root = domains_root.resolve()
    domain_dir = (root / domain_id).resolve()
    if root != domain_dir and root not in domain_dir.parents:
        raise KeyError(f"Unknown domain_id {domain_id!r}")
    if not domain_dir.exists():
        raise KeyError(f"Unknown domain_id {domain_id!r}")
    return domain_dir


def safe_child_file(parent: Path, identifier: str, suffix: str) -> Path:
    if not SAFE_SYSTEM_ID_RE.fullmatch(identifier):
        raise KeyError(f"Unknown system_id {identifier!r}")
    root = parent.resolve()
    child = (root / f"{identifier}{suffix}").resolve()
    if root != child.parent:
        raise KeyError(f"Unknown system_id {identifier!r}")
    return child
