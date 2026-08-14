"""Command-line interface for rzip."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import click

from rzip.packer import pack


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(package_name="rzip")
def cli() -> None:
    """rzip — ZIP a project while respecting .gitignore."""


@cli.command()
@click.argument("project_path", type=click.Path(exists=True, file_okay=False, resolve_path=True))
@click.option(
    "-o", "--output",
    type=click.Path(dir_okay=False, resolve_path=True),
    default=None,
    help="Output ZIP file path.  Defaults to <project_name>.zip.",
)
@click.option("--verbose", "-v", is_flag=True, help="Show included and excluded files.")
@click.option("--dry-run", is_flag=True, help="List files without creating a ZIP.")
def pack_cmd(
    project_path: str,
    output: Optional[str],
    verbose: bool,
    dry_run: bool,
) -> None:
    """Pack a project directory into a ZIP archive."""
    try:
        pack(
            project_path=project_path,
            output_zip=output,
            verbose=verbose,
            dry_run=dry_run,
        )
    except (FileNotFoundError, NotADirectoryError) as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


def main() -> None:
    """Entry point for the ``rzip`` console script."""
    cli()


if __name__ == "__main__":
    main()
