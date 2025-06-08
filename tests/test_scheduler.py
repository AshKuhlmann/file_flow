import pytest
from sorter import scheduler
from sorter.scheduler import validate_cron


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
