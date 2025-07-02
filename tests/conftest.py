import sys
from pathlib import Path
import io
import contextlib
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sorter.cli import main  # noqa: E402


def run_cli(args):
    buf = io.StringIO()
    exit_code = 0
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        try:
            main(args)
        except SystemExit as e:
            exit_code = int(e.code or 0)
    return SimpleNamespace(exit_code=exit_code, stdout=buf.getvalue())
