import os
import re
import subprocess
import sys
from unittest.mock import patch

from arlogi._rotation import prune_archives


def test_prune_archives_ignores_directories_and_symlinks(tmp_path):
    pattern = re.compile(r"^app-(?P<stamp>\d{4}-\d{2}-\d{2})(?:\.(?P<suffix>\d+))?\.jsonl$")
    real_old = tmp_path / "app-2026-06-10.jsonl"
    real_new = tmp_path / "app-2026-06-11.jsonl"
    real_old.write_text("old\n", encoding="utf-8")
    real_new.write_text("new\n", encoding="utf-8")
    os.utime(real_old, ns=(1_000_000_000, 1_000_000_000))
    os.utime(real_new, ns=(2_000_000_000, 2_000_000_000))

    matching_dir = tmp_path / "app-2026-06-15.jsonl"
    matching_dir.mkdir()
    os.utime(matching_dir, ns=(5_000_000_000, 5_000_000_000))

    matching_symlink = tmp_path / "app-2026-06-16.jsonl"
    matching_symlink.symlink_to(real_new)

    prune_archives(tmp_path, pattern, keep=1)

    assert not real_old.exists()
    assert real_new.exists()
    assert matching_dir.is_dir()
    assert matching_symlink.is_symlink()


def test_prune_archives_deterministic_tie_breaker_on_equal_mtime(tmp_path):
    pattern = re.compile(r"^x-(?P<stamp>\d{4}-\d{2}-\d{2})(?:\.(?P<suffix>\d+))?\.jsonl$")
    names = ["x-2026-06-10.jsonl", "x-2026-06-10.1.jsonl", "x-2026-06-10.2.jsonl", "x-2026-06-10.10.jsonl"]
    equal_ns = 1_700_000_000_000_000_000
    for name in names:
        path = tmp_path / name
        path.write_text(f"{name}\n", encoding="utf-8")
        os.utime(path, ns=(equal_ns, equal_ns))

    prune_archives(tmp_path, pattern, keep=2)

    surviving = sorted(p.name for p in tmp_path.iterdir())
    assert surviving == ["x-2026-06-10.10.jsonl", "x-2026-06-10.2.jsonl"]


def test_prune_archives_excludes_active_file_by_resolved_path(tmp_path):
    real_dir = tmp_path / "real"
    real_dir.mkdir()
    active = real_dir / "app-2026-06-10.jsonl"
    older = real_dir / "app-2026-06-09.jsonl"
    active.write_text("active\n", encoding="utf-8")
    older.write_text("older\n", encoding="utf-8")
    os.utime(active, ns=(1_000_000_000, 1_000_000_000))
    os.utime(older, ns=(2_000_000_000, 2_000_000_000))

    link_dir = tmp_path / "link_dir"
    link_dir.symlink_to(real_dir)

    pattern = re.compile(r"^app-(?P<stamp>\d{4}-\d{2}-\d{2})(?:\.(?P<suffix>\d+))?\.jsonl$")
    prune_archives(real_dir, pattern, keep=0, active_path=link_dir / "app-2026-06-10.jsonl")

    assert active.exists()
    assert not older.exists()


def test_prune_archives_swallows_os_errors(tmp_path):
    pattern = re.compile(r"^app-(?P<stamp>\d{4}-\d{2}-\d{2})(?:\.(?P<suffix>\d+))?\.jsonl$")
    (tmp_path / "app-2026-06-01.jsonl").write_text("a\n", encoding="utf-8")
    (tmp_path / "app-2026-06-02.jsonl").write_text("b\n", encoding="utf-8")

    with patch("os.scandir", side_effect=OSError("scandir fail")):
        prune_archives(tmp_path, pattern, keep=1)

    with patch("os.unlink", side_effect=OSError("unlink fail")):
        prune_archives(tmp_path, pattern, keep=1)

    assert (tmp_path / "app-2026-06-01.jsonl").exists()
    assert (tmp_path / "app-2026-06-02.jsonl").exists()


def test_core_and_rotation_import_loads_no_opentelemetry():
    code = (
        "import sys; "
        "import arlogi; "
        "import arlogi._rotation; "
        "otel_mods = [m for m in sys.modules if m == 'opentelemetry' or m.startswith('opentelemetry.')]; "
        "assert otel_mods == [], f'Unexpected opentelemetry imports: {otel_mods}'"
    )
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=False)
    assert proc.returncode == 0, proc.stderr
