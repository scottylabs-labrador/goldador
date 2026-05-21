from contextlib import contextmanager
from functools import wraps
from typing import TYPE_CHECKING, ParamSpec, TypeVar

from meta.models import Team

from ._app_logger import get_app_logger

P = ParamSpec("P")
R = TypeVar("R")

if TYPE_CHECKING:
    from collections.abc import Callable, Generator


def print_section(section: str) -> None:
    """Print the header banner of a section."""
    logger = get_app_logger()
    logger.print_bold("=" * 50)
    logger.print_bold("%s...", section)
    logger.print_bold("=" * 50 + "\n")


@contextmanager
def log_operation(operation_name: str) -> Generator[None]:
    """Context manager to log when an operation starts, finishes, or fails.

    When an exception occurs, it is logged and the traceback is printed,
    and the exception is re-raised.
    """
    logger = get_app_logger()
    logger.info("Starting to %s...", operation_name)
    try:
        yield
        logger.success("Successfully %s.\n", operation_name)
    except Exception:
        # We raise the exception again so we don't use logger.exception() here
        # to prevent duplciated traceback printing.
        logger.error("Failed to %s:", operation_name)  # noqa: TRY400
        raise


def log_team_sync() -> Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        """Decorate a team sync function to log around it.

        Team should always be the second argument of the team sync function.
        """

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            team = args[2]
            if not isinstance(team, Team):
                # Raise an error here since this is purely a programming error
                msg = "Third argument must be a Team"
                raise TypeError(msg)

            logger = get_app_logger()
            logger.print_bold("Syncing team %s...\n", team.name)
            result = func(*args, **kwargs)
            logger.print("")
            return result

        return wrapper

    return decorator
