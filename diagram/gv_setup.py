"""Make sure the Graphviz `dot` engine can be found and executed.

Why this exists
---------------
The `graphviz` PyPI package is only a thin wrapper that shells out to the Graphviz
*system binaries* (`dot`, `neato`, ...). Those binaries are a separate install.

* On Streamlit Community Cloud, the `packages.txt` file (containing `graphviz`)
  installs the binaries onto PATH, so `ensure_graphviz_on_path()` finds `dot`
  immediately and does nothing else.
* On a local Windows machine without an admin install, users often only have a
  *portable* copy of Graphviz unpacked somewhere under %LOCALAPPDATA% or
  Program Files. This helper locates that copy and prepends its `bin` directory
  to PATH for the current process, so no admin install is required.

Call `ensure_graphviz_on_path()` once, early, before rendering anything.
"""

from __future__ import annotations

import glob
import os
import shutil
from typing import List


def _candidate_bin_dirs() -> List[str]:
    """Return plausible Graphviz `bin` directories on this machine (Windows-focused)."""
    dirs: List[str] = []
    local = os.environ.get("LOCALAPPDATA", "")
    pf = os.environ.get("ProgramFiles", r"C:\Program Files")
    pf86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")

    patterns = []
    if local:
        # Portable unzip, e.g. %LOCALAPPDATA%\Graphviz\Graphviz-15.1.1-win64\bin
        patterns.append(os.path.join(local, "Graphviz", "**", "bin"))
    patterns.append(os.path.join(pf, "Graphviz*", "bin"))
    patterns.append(os.path.join(pf86, "Graphviz*", "bin"))

    for pattern in patterns:
        for path in glob.glob(pattern, recursive=True):
            if os.path.isdir(path) and (
                os.path.exists(os.path.join(path, "dot.exe"))
                or os.path.exists(os.path.join(path, "dot"))
            ):
                dirs.append(path)
    return dirs


def ensure_graphviz_on_path() -> bool:
    """Return True if a runnable `dot` engine is on PATH after this call.

    If `dot` is already resolvable, returns True without touching PATH. Otherwise
    searches for a portable/installed copy and prepends its bin dir to PATH.
    """
    if shutil.which("dot"):
        return True

    for bin_dir in _candidate_bin_dirs():
        os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")
        if shutil.which("dot"):
            return True

    return shutil.which("dot") is not None
