"""Abstract synchronizer class."""

from abc import ABC, abstractmethod

from meta.loaders import load_members, load_teams
from meta.logger import get_app_logger

from ._constants import LEADERSHIP
from .leadership import set_leadership_from_grouper


class AbstractSynchronizer(ABC):
    """Abstract synchronizer class."""

    @abstractmethod
    def __init__(
        self,
    ) -> None:
        """Initialize the AbstractSynchronizer.

        Sets the members and teams, with leadership set from Grouper, and
        creates a logger.
        """
        self.members = load_members()
        self.teams = load_teams()
        set_leadership_from_grouper(self.teams[LEADERSHIP], self.members)
        self.logger = get_app_logger()

    @abstractmethod
    def sync(self) -> None:
        """Synchronize the members and teams."""
        msg = "Subclasses must implement this method"
        raise NotImplementedError(msg)


__all__ = ["AbstractSynchronizer"]
