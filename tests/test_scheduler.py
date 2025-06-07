import pytest

from sorter.scheduler import validate_cron


@pytest.mark.parametrize("expr", ["0 0 * * *", "15 4 * * 1-5"])
def test_valid_cron(expr):
    validate_cron(expr)  # should not raise


@pytest.mark.parametrize("expr", ["bad", "61 0 * * *", "* * *"])
def test_invalid_cron(expr):
    with pytest.raises(ValueError):
        validate_cron(expr)
