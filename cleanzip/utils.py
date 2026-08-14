"""Utility helpers for cleanzip."""

from __future__ import annotations

import pathlib
from typing import List

import pathspec


# Patterns that are always excluded regardless of .gitignore content.
_BUILTIN_EXCLUDES: List[str] = [
    ".git",
    ".git/**",
]

# Default .gitignore content written when no .gitignore is found.
_DEFAULT_GITIGNORE = """\
# Created by cleanzip — common files to exclude from ZIP archives.

# Python
venv/
.venv/
env/
__pycache__/
*.pyc
*.pyo

# Node
node_modules/

# Version control
.git/

# IDE / Editor
.vscode/
.idea/

# Build output
build/
dist/
target/
coverage/

# Test / lint caches
.pytest_cache/
.mypy_cache/

# Framework caches
.next/
.nuxt/

# Temporary files
tmp/
temp/
.cache/
*.log

# OS
.DS_Store
Thumbs.db

# Secrets
.env
"""


def _ensure_gitignore(project_path: pathlib.Path) -> None:
    """Create a default ``.gitignore`` in *project_path* if one does not exist."""
    gitignore = project_path / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text(_DEFAULT_GITIGNORE, encoding="utf-8")
        print(f"Created default .gitignore in {project_path}")


def load_gitignore_spec(
    project_path: pathlib.Path,
) -> pathspec.PathSpec:
    """Read ``.gitignore`` from *project_path* and return a compiled PathSpec.

    If no ``.gitignore`` exists, a default one is created automatically
    containing common patterns for Python, Node, IDEs, OS files, and build
    artifacts.  Built-in excludes (e.g. ``.git/``) are always appended.
    """
    _ensure_gitignore(project_path)

    patterns: List[str] = list(_BUILTIN_EXCLUDES)

    gitignore = project_path / ".gitignore"
    text = gitignore.read_text(encoding="utf-8", errors="surrogateescape")
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            patterns.append(stripped)

    return pathspec.PathSpec.from_lines("gitignore", patterns)



def collect_files(
    project_path: pathlib.Path,
    spec: pathspec.PathSpec,
    *,
    verbose: bool = False,
) -> List[pathlib.Path]:
    """Walk *project_path* and return relative paths not matched by *spec*.

    Directories matched by the spec are pruned so their contents are never
    visited, which keeps the function fast on large trees.

    When *verbose* is ``True`` included/excluded paths are printed to stdout.
    """
    included: List[pathlib.Path] = []

    # Use a stack-based walk so we can prune directories early.
    dirs_to_visit: List[pathlib.Path] = [project_path]

    while dirs_to_visit:
        current = dirs_to_visit.pop()
        try:
            children = sorted(current.iterdir())
        except PermissionError:
            if verbose:
                rel = current.relative_to(project_path)
                print(f"  SKIP (permission denied): {rel}")
            continue

        for child in children:
            try:
                rel = child.relative_to(project_path)
            except ValueError:
                continue

            # Normalize to forward-slash POSIX string for pathspec matching.
            rel_posix = rel.as_posix()
            if child.is_dir():
                rel_posix += "/"

            if spec.match_file(rel_posix):
                if verbose:
                    print(f"  EXCLUDE: {rel}")
                continue

            if child.is_dir():
                dirs_to_visit.append(child)
            elif child.is_file():
                if verbose:
                    print(f"  INCLUDE: {rel}")
                included.append(rel)

    included.sort()
    return included
