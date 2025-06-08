import importlib
import sys

import pytest


def test_import_without_dsn(monkeypatch):
    monkeypatch.delenv("FILE_SORTER_SENTRY_DSN", raising=False)
    if "sentry_sdk" in sys.modules:
        del sys.modules["sentry_sdk"]
    import sorter.telemetry as tel

    importlib.reload(tel)


def test_import_with_dsn(monkeypatch):
    events = []

    class FakeSdk:
        def init(self, dsn, traces_sample_rate=1.0):
            events.append((dsn, traces_sample_rate))

    monkeypatch.setenv("FILE_SORTER_SENTRY_DSN", "abc")
    monkeypatch.setitem(sys.modules, "sentry_sdk", FakeSdk())
    import sorter.telemetry as tel

    importlib.reload(tel)
    assert events == [("abc", 0.0)]
