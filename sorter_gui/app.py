from __future__ import annotations

import pathlib
import sys
import threading
import queue

from typing import Any, Iterable

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QProgressBar,
)

from sorter import build_report, move_with_log, plan_moves
from sorter.rollback import rollback


def _build_mapping(
    paths: Iterable[pathlib.Path], dest_root: pathlib.Path
) -> list[tuple[pathlib.Path, pathlib.Path]]:
    return plan_moves(list(paths), dest_root)


class MainWindow(QMainWindow):  # type: ignore[misc]
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("File Sorter")
        self._mapping: list[tuple[pathlib.Path, pathlib.Path]] = []
        self._last_log: pathlib.Path | None = None
        self.task_queue: queue.Queue = queue.Queue()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._check_queue)
        self._worker_thread: threading.Thread | None = None
        self._done_callback: Any | None = None
        self._build_ui()

    # ---------------- UI setup -----------------
    def _build_ui(self) -> None:
        central = QWidget()
        vbox = QVBoxLayout(central)

        self.dir_list = QListWidget()
        vbox.addWidget(QLabel("Scan Directories:"))
        vbox.addWidget(self.dir_list)

        h_add = QHBoxLayout()
        btn_add = QPushButton("Add Folder…")
        btn_add.clicked.connect(self._add_folder)
        h_add.addWidget(btn_add)
        vbox.addLayout(h_add)

        h_dest = QHBoxLayout()
        self.dest_edit = QLineEdit()
        browse = QPushButton("Browse…")
        browse.clicked.connect(self._browse_dest)
        h_dest.addWidget(QLabel("Destination:"))
        h_dest.addWidget(self.dest_edit)
        h_dest.addWidget(browse)
        vbox.addLayout(h_dest)

        self.dry_run = QCheckBox("Dry-run only")
        vbox.addWidget(self.dry_run)

        h_btn = QHBoxLayout()
        self.btn_report = QPushButton("Generate Report")
        self.btn_report.clicked.connect(self._on_report)
        self.btn_move = QPushButton("Move Files")
        self.btn_move.setEnabled(False)
        self.btn_move.clicked.connect(self._on_move)
        h_btn.addWidget(self.btn_report)
        h_btn.addWidget(self.btn_move)
        vbox.addLayout(h_btn)

        self.progress = QProgressBar()
        self.progress.setMaximum(100)
        vbox.addWidget(self.progress)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        vbox.addWidget(QLabel("Log:"))
        vbox.addWidget(self.log)

        self.setCentralWidget(central)

    # -------------- helper methods --------------
    def _log(self, text: str) -> None:
        """Append *text* to the log widget."""
        self.log.append(text)

    def _start_thread(self, fn: Any, callback: Any) -> None:
        """Run *fn* in a background thread and call *callback* when done."""
        self._done_callback = callback
        self._worker_thread = threading.Thread(target=fn, daemon=True)
        self._worker_thread.start()
        self.timer.start(100)

    def _check_queue(self) -> None:
        """Process messages from the worker thread."""
        try:
            msg_type, data = self.task_queue.get_nowait()
        except queue.Empty:
            if self._worker_thread and not self._worker_thread.is_alive():
                self.timer.stop()
            return

        if msg_type == "progress":
            self.progress.setValue(int(data))
        elif msg_type == "done":
            self.timer.stop()
            self.progress.setValue(0)
            if self._done_callback:
                self._done_callback(data)
            self._worker_thread = None
        elif msg_type == "error":
            self.timer.stop()
            self.progress.setValue(0)
            self._log(f"Error: {data}")
            self.btn_report.setEnabled(True)
            self.btn_move.setEnabled(True)
            self._worker_thread = None

    def _add_folder(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if path:
            QListWidgetItem(path, self.dir_list)

    def _browse_dest(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select Destination")
        if path:
            self.dest_edit.setText(path)

    # -------------- actions ---------------------
    def _on_report(self) -> None:
        paths = [
            pathlib.Path(self.dir_list.item(i).text())
            for i in range(self.dir_list.count())
        ]
        dest = pathlib.Path(self.dest_edit.text())
        if not paths or not dest:
            QMessageBox.warning(
                self, "Missing Input", "Please select folders and destination"
            )
            return
        dry = self.dry_run.isChecked()

        def work() -> None:
            try:
                mapping = _build_mapping(paths, dest)
                report = build_report(mapping, auto_open=True)
                self.task_queue.put(("done", (mapping, report, dry)))
            except Exception as exc:
                self.task_queue.put(("error", str(exc)))

        def done(
            result: tuple[
                list[tuple[pathlib.Path, pathlib.Path]],
                pathlib.Path,
                bool,
            ]
        ) -> None:
            mapping, report, dry_flag = result
            self._mapping = mapping
            self.btn_move.setEnabled(not dry_flag)
            self._log(f"Report saved to {report}")
            self.btn_report.setEnabled(True)

        self.btn_report.setEnabled(False)
        self.btn_move.setEnabled(False)
        self._start_thread(work, done)

    def _on_move(self) -> None:
        if not self._mapping:
            return
        if (
            QMessageBox.question(
                self,
                "Confirm",
                "Move the files now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            != QMessageBox.StandardButton.Yes
        ):
            return

        def work() -> None:
            try:
                log_path = move_with_log(self._mapping, show_progress=False)
                self.task_queue.put(("progress", 100))
                self.task_queue.put(("done", log_path))
            except Exception as exc:
                self.task_queue.put(("error", str(exc)))

        def done(log_path: pathlib.Path) -> None:
            self._last_log = log_path
            self._log(f"Done. Log at {log_path}")
            mb = QMessageBox(self)
            mb.setWindowTitle("Completed")
            mb.setText(f"Move complete. Log at {log_path}")
            undo_btn = mb.addButton("Undo Last Run", QMessageBox.ButtonRole.ActionRole)
            mb.addButton(QMessageBox.StandardButton.Ok)
            mb.exec()
            if mb.clickedButton() == undo_btn:
                rollback(log_path)
                self._log("Rollback complete")
            self.btn_report.setEnabled(True)
            self.btn_move.setEnabled(True)

        self.btn_move.setEnabled(False)
        self.btn_report.setEnabled(False)
        self._start_thread(work, done)


def main() -> None:
    app = QApplication(sys.argv)
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec())


if __name__ == "__main__":  # pragma: no cover - manual start
    main()
