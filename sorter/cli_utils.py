import functools
import logging
import typer

log = logging.getLogger(__name__)


def handle_cli_errors(func):
    """Wrap Typer command functions with common error handling."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileExistsError as exc:
            msg = f"Move aborted: destination already exists ({exc})"
            log.error(msg)
            typer.echo(msg)
        except FileNotFoundError as exc:
            msg = f"Log file not found: {exc}"
            log.error(msg)
            typer.echo(msg)
        except ModuleNotFoundError as exc:
            msg = (
                f"Missing dependency '{exc.name}'. Install optional extras to use this command."
            )
            log.error(msg)
            typer.echo(msg)
        except PermissionError as exc:
            msg = f"Permission denied: {exc}"
            log.error(msg)
            typer.echo(msg)
        except ValueError as exc:
            msg = str(exc)
            log.error(msg)
            typer.echo(msg)
        except Exception as exc:  # pragma: no cover - defensive
            log.exception("Unexpected error: %s", exc)
        else:
            return
        raise typer.Exit(1)

    return wrapper

__all__ = ["handle_cli_errors"]
