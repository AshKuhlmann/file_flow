import os
import pytest

os.environ["QT_QPA_PLATFORM"] = "offscreen"

try:  # noqa: E402
    from sorter_gui.app import MainWindow
except Exception as exc:  # pragma: no cover - optional dependency
    pytest.skip(f"PyQt not available: {exc}", allow_module_level=True)


def test_main_window_creation(qtbot):
    mw = MainWindow()
    qtbot.addWidget(mw)
    assert mw.windowTitle() == "File Sorter"
    assert mw.dir_list is not None
    assert mw.dest_edit is not None
