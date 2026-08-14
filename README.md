# rzip

> ZIP a project while respecting `.gitignore` — no Git required.

**rzip** creates a clean ZIP archive of your project, automatically excluding every file and folder matched by your `.gitignore`. It works even when the project is **not** a Git repository and never shells out to `git`.

Perfect for sharing code with AI code reviewers, teammates, or archival — without dragging along `node_modules/`, `__pycache__/`, or `.env` files.

---

## Features

- 🚀 **Fast** — prunes ignored directories early, never walks into them.
- 🔒 **No Git dependency** — reads `.gitignore` directly with [`pathspec`](https://pypi.org/project/pathspec/).
- 🌍 **Cross-platform** — Windows, macOS, Linux.
- 🗂️ **Preserves structure** — directory tree inside the ZIP mirrors the project.
- 🦄 **Unicode-safe** — handles non-ASCII file names.
- 📦 **Minimal dependencies** — only `pathspec` + `click`.

---

## Installation

```bash
pip install rzip
```

Or install from source:

```bash
git clone https://github.com/rzip/rzip.git
cd rzip
pip install -e ".[dev]"
```

---

## Quick Start

### CLI

```bash
# Pack the current directory
rzip pack .

# Specify output name
rzip pack . -o project.zip

# See what would be included/excluded
rzip pack . --verbose

# Dry run — no ZIP created
rzip pack . --dry-run
```

### Python API

```python
from rzip import pack

# Basic usage
pack("my_project")

# With options
pack(
    project_path="my_project",
    output_zip="my_project.zip",
    verbose=True,
)

# Dry run
pack("my_project", dry_run=True)
```

---

## CLI Reference

```text
Usage: rzip pack [OPTIONS] PROJECT_PATH

  Pack a project directory into a ZIP archive.

Options:
  -o, --output PATH   Output ZIP file path. Defaults to <project_name>.zip.
  -v, --verbose        Show included and excluded files.
  --dry-run            List files without creating a ZIP.
  -h, --help           Show this message and exit.
```

---

## How It Works

1. Reads `.gitignore` from the project root (gracefully skips if missing).
2. Always excludes `.git/` regardless of `.gitignore` contents.
3. Walks the directory tree, pruning ignored directories early for speed.
4. Writes non-ignored files into a deflated ZIP archive.

---

## Development

```bash
pip install -e ".[dev]"
pytest
```

---

## License

[MIT](LICENSE)
