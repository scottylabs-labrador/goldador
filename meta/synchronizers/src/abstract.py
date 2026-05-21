"""Abstract synchronizer class."""

from abc import ABC, abstractmethod

from meta.loaders import load_members, load_teams
from meta.logger import get_app_logger


class AbstractSynchronizer(ABC):
    """Abstract synchronizer class."""

    @abstractmethod
    def __init__(
        self,
    ) -> None:
        """Initialize the AbstractSynchronizer.

        Sets the members and teams and creates a logger.
        """
        self.members = load_members()
        self.teams = load_teams()
        self.logger = get_app_logger()

    @abstractmethod
    def sync(self) -> None:
        """Synchronize the members and teams."""
        msg = "Subclasses must implement this method"
        raise NotImplementedError(msg)


__all__ = ["AbstractSynchronizer"]
