import pytest
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "scheduler", Path(__file__).resolve().parents[1] / "sorter" / "scheduler.py"
)
assert spec is not None
scheduler = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(scheduler)
validate_cron = scheduler.validate_cron


@pytest.mark.parametrize("expr", ["0 0 * * *", "15 4 * * 1-5"])
def test_valid_cron(expr):
    validate_cron(expr)  # should not raise


@pytest.mark.parametrize("expr", ["bad", "61 0 * * *", "* * *"])
def test_invalid_cron(expr):
    with pytest.raises(ValueError):
        validate_cron(expr)


def test_install_job_linux(monkeypatch, tmp_path):
    called = {}
    monkeypatch.setattr(scheduler.platform, "system", lambda: "Linux")
    monkeypatch.setattr(
        scheduler, "_install_cron", lambda c, cmd: called.setdefault("cron", (c, cmd))
    )
    monkeypatch.setattr(
        scheduler,
        "_install_windows",
        lambda c, cmd: (_ for _ in ()).throw(AssertionError()),
    )

    scheduler.install_job("0 1 * * *", dirs=[tmp_path], dest=tmp_path / "d")
    assert called["cron"][0] == "0 1 * * *"


def test_install_job_windows(monkeypatch, tmp_path):
    called = {}
    monkeypatch.setattr(scheduler.platform, "system", lambda: "Windows")
    monkeypatch.setattr(
        scheduler, "_install_windows", lambda c, cmd: called.setdefault("win", (c, cmd))
    )
    monkeypatch.setattr(
        scheduler,
        "_install_cron",
        lambda c, cmd: (_ for _ in ()).throw(AssertionError()),
    )

    scheduler.install_job("0 2 * * *", dirs=[tmp_path], dest=tmp_path / "d")
    assert called["win"][0] == "0 2 * * *"


def test_install_cron(monkeypatch):
    recorded = {}

    def fake_run(args, *, capture_output=False, text=False, input=None, check=False):
        if args == ["crontab", "-l"]:
            return type("R", (), {"stdout": ""})()
        recorded["args"] = args
        recorded["input"] = input
        return type("R", (), {})()

    monkeypatch.setattr(scheduler.subprocess, "run", fake_run)
    scheduler._install_cron("0 3 * * *", "cmd")
    assert recorded["args"] == ["crontab", "-"]
    assert "cmd && file-sorter report --auto-open" in recorded["input"]


def test_install_windows(monkeypatch, tmp_path):
    captured = {}

    def fake_run(args, *, check=False):
        captured["args"] = args
        return type("R", (), {})()

    monkeypatch.setattr(scheduler.subprocess, "run", fake_run)
    monkeypatch.setenv("TEMP", str(tmp_path))

    scheduler._install_windows("0 0 * * *", "cmd")

    xml_file = tmp_path / "Task.xml"
    assert xml_file.exists()
    content = xml_file.read_text()
    assert "<Command>cmd</Command>" in content
    assert "<StartBoundary>2024-01-01T00:00:00</StartBoundary>" in content
    assert "/XML" in captured["args"]
    assert str(xml_file) in captured["args"]

def test_install_cron_entry(monkeypatch):
    out = {}
    def fake_run(args, *, capture_output=False, text=False, input=None, check=False):
        if args == ["crontab", "-l"]:
            return type("R", (), {"stdout": "# file-sorter\n"})()
        out['args'] = args
        out['input'] = input
        return type("R", (), {})()
    monkeypatch.setattr(scheduler.subprocess, "run", fake_run)
    scheduler._install_cron("15 5 * * *", "cmd")
    assert "15 5 * * * cmd && file-sorter report --auto-open" in out['input']
    assert out['input'].startswith("# file-sorter")
