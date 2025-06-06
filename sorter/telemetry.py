"""Sentry init stub; safe-import when DSN absent."""

import os
from contextlib import suppress

_DSN = os.getenv("FILE_SORTER_SENTRY_DSN")
if _DSN:
    with suppress(ImportError):
        import sentry_sdk

        sentry_sdk.init(_DSN, traces_sample_rate=0.0)
