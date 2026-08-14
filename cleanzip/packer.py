"""Core packing logic for cleanzip."""

from __future__ import annotations

import pathlib
import sys
import zipfile
from typing import List, Optional, Union

from cleanzip.utils import collect_files, load_gitignore_spec


def pack(
    project_path: Union[str, pathlib.Path],
    output_zip: Optional[Union[str, pathlib.Path]] = None,
    *,
    verbose: bool = False,
    dry_run: bool = False,
) -> Optional[pathlib.Path]:
    """Create a ZIP archive of *project_path*, excluding .gitignore'd files.

    Parameters
    ----------
    project_path:
        Root directory of the project to pack.
    output_zip:
        Destination path for the ZIP file.  When ``None`` the archive is
        named ``<directory_name>.zip`` and placed next to the project.
    verbose:
        Print every included / excluded file.
    dry_run:
        List what *would* be zipped but do not create the archive.

    Returns
    -------
    pathlib.Path or None
        The path to the created ZIP file, or ``None`` when *dry_run* is
        ``True``.

    Raises
    ------
    FileNotFoundError
        If *project_path* does not exist.
    NotADirectoryError
        If *project_path* is not a directory.
    """
    project_path = pathlib.Path(project_path).resolve()

    if not project_path.exists():
        raise FileNotFoundError(f"Path does not exist: {project_path}")
    if not project_path.is_dir():
        raise NotADirectoryError(f"Not a directory: {project_path}")

    # Resolve output path.
    if output_zip is None:
        output_zip = project_path.parent / f"{project_path.name}.zip"
    else:
        output_zip = pathlib.Path(output_zip).resolve()

    spec = load_gitignore_spec(project_path)

    if verbose:
        print(f"Project : {project_path}")
        print(f"Output  : {output_zip}")
        print()

    files: List[pathlib.Path] = collect_files(
        project_path, spec, verbose=verbose,
    )

    if dry_run:
        print(f"Dry run — {len(files)} file(s) would be archived:")
        for f in files:
            print(f"  {f}")
        return None

    # Warn (but do not fail) if target ZIP already exists.
    if output_zip.exists():
        print(f"Overwriting existing file: {output_zip}", file=sys.stderr)

    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel in files:
            abs_path = project_path / rel
            zf.write(abs_path, arcname=str(rel))

    print(f"Created: {output_zip.name}")
    return output_zip
