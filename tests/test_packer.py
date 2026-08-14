"""Tests for rzip.packer and rzip.utils."""

from __future__ import annotations

import pathlib
import zipfile

import pytest

from rzip.packer import pack
from rzip.utils import collect_files, load_gitignore_spec


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_project(tmp_path: pathlib.Path) -> pathlib.Path:
    """Create a small project tree with a .gitignore."""
    proj = tmp_path / "myproject"
    proj.mkdir()

    # Source files
    (proj / "main.py").write_text("print('hello')\n", encoding="utf-8")
    (proj / "README.md").write_text("# My Project\n", encoding="utf-8")

    # Nested directory
    pkg = proj / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "core.py").write_text("x = 1\n", encoding="utf-8")

    # Directories / files that should be ignored
    node = proj / "node_modules"
    node.mkdir()
    (node / "dep.js").write_text("//dep\n", encoding="utf-8")

    cache = proj / "__pycache__"
    cache.mkdir()
    (cache / "main.cpython-312.pyc").write_bytes(b"\x00")

    (proj / ".env").write_text("SECRET=abc\n", encoding="utf-8")
    (proj / "debug.log").write_text("log line\n", encoding="utf-8")

    # .gitignore
    gitignore = (
        "node_modules/\n"
        "__pycache__/\n"
        ".env\n"
        "*.log\n"
    )
    (proj / ".gitignore").write_text(gitignore, encoding="utf-8")

    return proj


@pytest.fixture()
def project_no_gitignore(tmp_path: pathlib.Path) -> pathlib.Path:
    """Project without a .gitignore file."""
    proj = tmp_path / "bare"
    proj.mkdir()
    (proj / "file.txt").write_text("data\n", encoding="utf-8")
    sub = proj / "sub"
    sub.mkdir()
    (sub / "nested.txt").write_text("nested\n", encoding="utf-8")
    return proj


@pytest.fixture()
def project_with_unicode(tmp_path: pathlib.Path) -> pathlib.Path:
    """Project containing files with Unicode names."""
    proj = tmp_path / "uni_proj"
    proj.mkdir()
    (proj / "café.txt").write_text("latte\n", encoding="utf-8")
    (proj / "日本語.md").write_text("こんにちは\n", encoding="utf-8")
    (proj / ".gitignore").write_text("*.log\n", encoding="utf-8")
    return proj


# ---------------------------------------------------------------------------
# Tests — .gitignore parsing
# ---------------------------------------------------------------------------

class TestLoadGitignoreSpec:
    def test_parses_gitignore(self, sample_project: pathlib.Path) -> None:
        spec = load_gitignore_spec(sample_project)
        assert spec.match_file("node_modules/")
        assert spec.match_file(".env")
        assert spec.match_file("debug.log")
        assert not spec.match_file("main.py")

    def test_missing_gitignore(self, project_no_gitignore: pathlib.Path) -> None:
        spec = load_gitignore_spec(project_no_gitignore)
        # Only built-in excludes active
        assert spec.match_file(".git/")
        assert not spec.match_file("file.txt")

    def test_always_excludes_git_dir(self, sample_project: pathlib.Path) -> None:
        spec = load_gitignore_spec(sample_project)
        assert spec.match_file(".git/")
        assert spec.match_file(".git/config")


# ---------------------------------------------------------------------------
# Tests — file collection
# ---------------------------------------------------------------------------

class TestCollectFiles:
    def test_excludes_ignored_files(self, sample_project: pathlib.Path) -> None:
        spec = load_gitignore_spec(sample_project)
        files = collect_files(sample_project, spec)
        names = {f.as_posix() for f in files}

        assert "main.py" in names
        assert "README.md" in names
        assert "pkg/__init__.py" in names
        assert "pkg/core.py" in names
        assert ".gitignore" in names

        # Ignored entries must be absent.
        for bad in ("node_modules/dep.js", ".env", "debug.log",
                    "__pycache__/main.cpython-312.pyc"):
            assert bad not in names, f"{bad} should have been excluded"

    def test_no_gitignore_includes_everything(self, project_no_gitignore: pathlib.Path) -> None:
        spec = load_gitignore_spec(project_no_gitignore)
        files = collect_files(project_no_gitignore, spec)
        names = {f.as_posix() for f in files}
        assert "file.txt" in names
        assert "sub/nested.txt" in names

    def test_unicode_filenames(self, project_with_unicode: pathlib.Path) -> None:
        spec = load_gitignore_spec(project_with_unicode)
        files = collect_files(project_with_unicode, spec)
        names = {f.as_posix() for f in files}
        assert "café.txt" in names
        assert "日本語.md" in names


# ---------------------------------------------------------------------------
# Tests — pack()
# ---------------------------------------------------------------------------

class TestPack:
    def test_creates_zip(self, sample_project: pathlib.Path, tmp_path: pathlib.Path) -> None:
        out = tmp_path / "out.zip"
        result = pack(sample_project, out)

        assert result == out
        assert out.exists()

        with zipfile.ZipFile(out) as zf:
            names = set(zf.namelist())

        assert "main.py" in names
        assert "pkg/core.py" in names
        # Ignored files must be absent.
        assert "node_modules/dep.js" not in names
        assert ".env" not in names

    def test_auto_names_zip(self, sample_project: pathlib.Path) -> None:
        result = pack(sample_project)
        assert result is not None
        assert result.name == "myproject.zip"
        assert result.exists()
        result.unlink()  # cleanup

    def test_dry_run_does_not_create_file(
        self, sample_project: pathlib.Path, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str],
    ) -> None:
        out = tmp_path / "should_not_exist.zip"
        result = pack(sample_project, out, dry_run=True)

        assert result is None
        assert not out.exists()

        captured = capsys.readouterr()
        assert "Dry run" in captured.out

    def test_verbose_output(
        self, sample_project: pathlib.Path, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str],
    ) -> None:
        out = tmp_path / "verbose.zip"
        pack(sample_project, out, verbose=True)

        captured = capsys.readouterr()
        assert "INCLUDE" in captured.out
        assert "EXCLUDE" in captured.out

    def test_nonexistent_path_raises(self, tmp_path: pathlib.Path) -> None:
        with pytest.raises(FileNotFoundError):
            pack(tmp_path / "nope")

    def test_file_instead_of_dir_raises(self, tmp_path: pathlib.Path) -> None:
        f = tmp_path / "afile.txt"
        f.write_text("hi")
        with pytest.raises(NotADirectoryError):
            pack(f)

    def test_overwrites_existing_zip(
        self, sample_project: pathlib.Path, tmp_path: pathlib.Path,
    ) -> None:
        out = tmp_path / "dup.zip"
        out.write_text("placeholder")
        result = pack(sample_project, out)
        assert result == out
        # Should be a valid ZIP now.
        with zipfile.ZipFile(out) as zf:
            assert len(zf.namelist()) > 0

    def test_nested_directory_structure(
        self, sample_project: pathlib.Path, tmp_path: pathlib.Path,
    ) -> None:
        out = tmp_path / "nested.zip"
        pack(sample_project, out)
        with zipfile.ZipFile(out) as zf:
            names = zf.namelist()
        # Ensure nested pkg files are included with correct paths.
        assert "pkg/__init__.py" in names
        assert "pkg/core.py" in names

    def test_missing_gitignore_includes_all(
        self, project_no_gitignore: pathlib.Path, tmp_path: pathlib.Path,
    ) -> None:
        out = tmp_path / "bare.zip"
        pack(project_no_gitignore, out)
        with zipfile.ZipFile(out) as zf:
            names = set(zf.namelist())
        assert "file.txt" in names
        assert "sub/nested.txt" in names
