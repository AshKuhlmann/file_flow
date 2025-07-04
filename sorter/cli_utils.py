import functools
import logging


__all__ = ["handle_cli_errors", "human_readable_size"]

log = logging.getLogger(__name__)


def handle_cli_errors(func):
    """Wrap command functions with common error handling."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileExistsError as exc:
            msg = f"Move aborted: destination already exists ({exc})"
        except FileNotFoundError as exc:
            msg = f"File not found: {exc}"
        except ModuleNotFoundError as exc:
            msg = (
                f"Missing dependency '{exc.name}'. Install optional extras "
                "to use this command."
            )
        except PermissionError as exc:
            msg = f"Permission denied: {exc}"
        except ValueError as exc:
            msg = str(exc)
        except Exception as exc:  # pragma: no cover - defensive
            log.exception("Unexpected error: %s", exc)
            raise SystemExit(1) from exc
        else:
            return

        log.error(msg)
        print(msg)
        raise SystemExit(1)

    return wrapper


def human_readable_size(size: int) -> str:
    """Convert *size* in bytes to a human readable string."""

    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    value = float(size)
    for unit in units:
        if value < 1024.0 or unit == units[-1]:
            return f"{value:.1f} {unit}"
        value /= 1024.0
    return f"{value:.1f} {units[-1]}"
