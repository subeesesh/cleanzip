"""Command-line interface for cleanzip."""

from __future__ import annotations

import sys
from typing import Optional

import click

from cleanzip.packer import pack as _pack


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(package_name="cleanzip")
def cli() -> None:
    """cleanzip — ZIP a project while respecting .gitignore.

    \b
    You can omit the 'pack' subcommand:
      cleanzip .
      cleanzip /path/to/project -o out.zip

    Or use it explicitly:
      cleanzip pack .
    """


@cli.command("pack")
@click.argument("project_path", default=".", required=False)
@click.option(
    "-o", "--output",
    type=click.Path(dir_okay=False, resolve_path=True),
    default=None,
    help="Output ZIP file path. Defaults to <project_name>.zip.",
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
        _pack(
            project_path=project_path,
            output_zip=output,
            verbose=verbose,
            dry_run=dry_run,
        )
    except (FileNotFoundError, NotADirectoryError) as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


def main() -> None:
    """Entry point for the ``cleanzip`` console script."""
    # If the first real argument is not a known subcommand (or a flag),
    # silently inject 'pack' so that `cleanzip .` works like `cleanzip pack .`
    known_subcommands = {"pack", "--help", "-h", "--version"}
    args = sys.argv[1:]
    first = args[0] if args else None
    if first is not None and first not in known_subcommands:
        sys.argv.insert(1, "pack")
    cli()


if __name__ == "__main__":
    main()
