import logging
import os
import pathlib
from typing import Set, Tuple


log = logging.getLogger(__name__)


FileId = Tuple[int, int]


def scan_paths(
    paths: list[pathlib.Path],
    *,
    follow_symlinks: bool = False,
    skip_hidden: bool = True,
) -> list[pathlib.Path]:
    """Recursively yield all regular files rooted at the given paths.

    Parameters
    ----------
    paths:
        Root paths to scan.
    follow_symlinks:
        Whether to follow symbolic links.
    skip_hidden:
        Skip hidden files and directories whose name starts with ``.``.

    Returns
    -------
    list[pathlib.Path]
        Sorted absolute paths of discovered regular files without duplicates.
    """

    result: list[pathlib.Path] = []
    seen_files: Set[FileId] = set()
    seen_dirs: Set[FileId] = set()

    def _scan_dir(dir_path: pathlib.Path) -> None:
        try:
            st = dir_path.stat(follow_symlinks=False)
        except OSError:
            return
        dir_id = (st.st_dev, st.st_ino)
        if dir_id in seen_dirs:
            return
        seen_dirs.add(dir_id)

        try:
            with os.scandir(dir_path) as it:
                for entry in it:
                    name = entry.name
                    if skip_hidden and name.startswith("."):
                        continue
                    entry_path = pathlib.Path(entry.path)
                    try:
                        if entry.is_symlink():
                            if not follow_symlinks:
                                continue
                            target_path = entry_path.resolve()
                        else:
                            target_path = entry_path

                        if entry.is_dir(follow_symlinks=follow_symlinks):
                            _scan_dir(target_path)
                        elif entry.is_file(follow_symlinks=follow_symlinks):
                            try:
                                st = entry.stat(follow_symlinks=follow_symlinks)
                            except OSError:
                                continue
                            fid: FileId = (st.st_dev, st.st_ino)
                            if fid in seen_files:
                                continue
                            seen_files.add(fid)
                            result.append(target_path.resolve())
                    except OSError:
                        continue
        except OSError:
            return

    for p in paths:
        p = pathlib.Path(p)
        if skip_hidden and p.name.startswith("."):
            continue
        if p.is_symlink() and not follow_symlinks:
            continue
        if p.is_file():
            try:
                st = p.stat()
            except OSError:
                continue
            fid = (st.st_dev, st.st_ino)
            if fid not in seen_files:
                seen_files.add(fid)
                result.append(p.resolve())
        elif p.is_dir():
            _scan_dir(p.resolve() if p.is_symlink() else p)

    result.sort()
    if log.isEnabledFor(logging.DEBUG):
        log.debug("Discovered %d files under %s", len(result), paths)
    return result
