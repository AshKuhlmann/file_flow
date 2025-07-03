from __future__ import annotations

import pathlib
import sys

from typing import Any, Iterable

from PyQt6.QtCore import QObject, pyqtSignal, QThread
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


class Worker(QObject):
    """Background worker object for long-running tasks."""

    finished = pyqtSignal(object)
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    error = pyqtSignal(str, str)

    def __init__(self, func: Any, *args: Any) -> None:
        super().__init__()
        self._func = func
        self._args = args

    def run(self) -> None:  # pragma: no cover - GUI thread
        try:
            result = self._func(self._emit_progress, *self._args)
        except Exception as exc:  # pragma: no cover - runtime guard
            self.log.emit(f"An error occurred: {exc}")
            self.error.emit("Operation Failed", f"A critical error occurred:\n\n{exc}")
        else:
            self.finished.emit(result)

    def _emit_progress(self, value: int, message: str | None = None) -> None:
        self.progress.emit(value)
        if message:
            self.log.emit(message)


class MainWindow(QMainWindow):  # type: ignore[misc]
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("File Sorter")
        self._mapping: list[tuple[pathlib.Path, pathlib.Path]] = []
        self._last_log: pathlib.Path | None = None
        self._worker_thread: QThread | None = None
        self._worker: Worker | None = None
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

    def _start_worker(self, worker: Worker, callback: Any) -> None:
        """Run *worker* in a background thread and call *callback* when done."""
        self._done_callback = callback
        thread = QThread(self)
        worker.moveToThread(thread)
        worker.progress.connect(self.update_progress_bar)
        worker.log.connect(self._log)
        worker.error.connect(self.show_error_message)
        worker.finished.connect(self._handle_done)
        thread.started.connect(worker.run)
        thread.start()
        self._worker_thread = thread
        self._worker = worker

    def _handle_done(self, result: Any) -> None:
        self.progress.setValue(0)
        if self._done_callback:
            self._done_callback(result)
        if self._worker_thread:
            self._worker_thread.quit()
            self._worker_thread.wait()
        self._worker_thread = None
        self._worker = None

    def update_progress_bar(self, value: int) -> None:
        self.progress.setValue(value)

    def show_error_message(self, title: str, message: str) -> None:
        QMessageBox.critical(self, title, message)
        self.btn_report.setEnabled(True)
        self.btn_move.setEnabled(True)

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

        def task(progress_cb: Any) -> tuple[
            list[tuple[pathlib.Path, pathlib.Path]], pathlib.Path, bool
        ]:
            mapping = _build_mapping(paths, dest)
            progress_cb(50, None)
            report = build_report(mapping, auto_open=True)
            progress_cb(100, None)
            return mapping, report, dry

        def done(
            result: tuple[list[tuple[pathlib.Path, pathlib.Path]], pathlib.Path, bool]
        ) -> None:
            mapping, report, dry_flag = result
            self._mapping = mapping
            self.btn_move.setEnabled(not dry_flag)
            self._log(f"Report saved to {report}")
            self.btn_report.setEnabled(True)

        self.btn_report.setEnabled(False)
        self.btn_move.setEnabled(False)
        self.progress.setValue(0)
        self._start_worker(Worker(task), done)

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

        def task(progress_cb: Any) -> pathlib.Path:
            def cb(percent: int, src: pathlib.Path) -> None:
                progress_cb(percent, f"Moved {src.name}")

            return move_with_log(
                self._mapping, show_progress=False, progress_callback=cb
            )

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
        self.progress.setValue(0)
        self._start_worker(Worker(task), done)


def main() -> None:
    app = QApplication(sys.argv)
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec())


if __name__ == "__main__":  # pragma: no cover - manual start
    main()
