"""Utility helpers for rzip."""

from __future__ import annotations

import pathlib
from typing import List

import pathspec


# Patterns that are always excluded regardless of .gitignore content.
_BUILTIN_EXCLUDES: List[str] = [
    ".git",
    ".git/**",
]


def load_gitignore_spec(
    project_path: pathlib.Path,
) -> pathspec.PathSpec:
    """Read ``.gitignore`` from *project_path* and return a compiled PathSpec.

    If the file does not exist an empty spec (matches nothing) is returned.
    Built-in excludes (e.g. ``.git/``) are always appended.
    """
    patterns: List[str] = list(_BUILTIN_EXCLUDES)

    gitignore = project_path / ".gitignore"
    if gitignore.is_file():
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
