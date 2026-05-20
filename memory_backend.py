"""
DEPRECATED — this file is no longer used.

Earlier versions of this track used the Messages-API Memory tool with a
client-side filesystem backend. We've since switched to the proper Managed
Agents `memory_stores` primitive, which mounts at /mnt/memory/ inside the
session container and is inspectable via the Console UI and the API.

See create_agent.py, run_session_1.py, run_session_2.py, and inspect_memory.py
for the current implementation.

You can safely delete this file.
"""

raise ImportError(
    "memory_backend is deprecated. The track now uses Managed Agents memory "
    "stores — see run_session_1.py for the current pattern."
)
