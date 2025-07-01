import os
os.environ["QT_QPA_PLATFORM"] = "offscreen"
from sorter_gui.app import MainWindow


def test_main_window_creation(qtbot):
    mw = MainWindow()
    qtbot.addWidget(mw)
    assert mw.windowTitle() == "File Sorter"
    assert mw.dir_list is not None
    assert mw.dest_edit is not None
