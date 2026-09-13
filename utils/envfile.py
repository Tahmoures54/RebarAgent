# utils/envfile.py
"""Load a dotenv file into os.environ without extra dependencies."""

from __future__ import annotations

import os
from typing import Optional


def load_env_file(path: str, override: bool = False) -> int:
    """Parse KEY=VALUE lines. Returns number of keys applied. Missing file is a no-op."""
    if not path or not os.path.isfile(path):
        return 0
    applied = 0
    try:
        with open(path, "r", encoding="utf-8") as fh:
            lines = fh.readlines()
    except OSError:
        return 0
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if not override and key in os.environ and os.environ.get(key, "") != "":
            continue
        os.environ[key] = value
        applied += 1
    return applied


def load_project_env(base_dir: Optional[str] = None, override: bool = False) -> int:
    root = base_dir or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return load_env_file(os.path.join(root, ".env"), override=override)
