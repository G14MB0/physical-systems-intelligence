from __future__ import annotations

import os
from pathlib import Path


Path(".state").mkdir(exist_ok=True)
os.environ["DATABASE_URL"] = "sqlite:///./.state/pytest-import.db"
os.environ["DOMAINS_ROOT"] = "app/domains"
os.environ["VECTOR_BACKEND"] = "memory"
os.environ["EMBEDDING_PROVIDER"] = "hash"
