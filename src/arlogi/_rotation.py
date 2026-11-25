"""Shared stdlib-only archive pruning helpers for rotating log and telemetry writers."""

import os
import re


def _entry_sort_key(
    entry: os.DirEntry[str],
    pattern: re.Pattern[str],
    active_real: str | None,
) -> tuple[int, str, int, str] | None:
    """Build a sort key tuple for a matching regular archive file, or None to skip."""
    match = pattern.match(entry.name)
    if match is None:
        return None
    try:
        if not entry.is_file(follow_symlinks=False):
            return None
    except OSError:
        return None

    if active_real is not None:
        try:
            if os.path.realpath(entry.path) == active_real:
                return None
        except OSError:
            pass

    try:
        mtime_ns = entry.stat(follow_symlinks=False).st_mtime_ns
    except OSError:
        return None

    groups = match.groupdict()
    stamp = groups.get("stamp") or ""
    suffix_raw = groups.get("suffix")
    suffix = int(suffix_raw) if suffix_raw else 0
    return (mtime_ns, stamp, suffix, entry.path)


def prune_archives(
    directory: str | os.PathLike[str],
    pattern: re.Pattern[str],
    keep: int,
    active_path: str | os.PathLike[str] | None = None,
) -> None:
    """Prune rotated archive files matching ``pattern``, keeping the newest ``keep`` files.

    Only regular files (evaluated without following symlinks) are counted and eligible
    for deletion. Archives are ordered newest-first by ``(st_mtime_ns, stamp, suffix)``.
    All filesystem errors are handled non-fatally.
    """
    keep_count = max(0, keep)
    active_real = os.path.realpath(active_path) if active_path is not None else None

    try:
        with os.scandir(directory) as entries:
            candidates = [
                item for entry in entries if (item := _entry_sort_key(entry, pattern, active_real)) is not None
            ]
    except OSError:
        return

    if len(candidates) <= keep_count:
        return

    candidates.sort(key=lambda item: (item[0], item[1], item[2]), reverse=True)
    for _, _, _, old_path in candidates[keep_count:]:
        try:
            os.unlink(old_path)
        except OSError:
            continue
