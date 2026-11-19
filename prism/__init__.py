"""prism - deterministic, offline resolution of AI coding-agent instruction context.

The core guarantee: prism never opens a socket, never spawns a process, and never
writes to the repository unless the user passes an explicit write flag.
"""

from __future__ import annotations

__version__ = "1.0.0"
__all__ = ["__version__", "audit", "resolve", "build_snapshot"]

from .api import audit, resolve, build_snapshot  # noqa: E402,F401
