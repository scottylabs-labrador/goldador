"""Codeowners synchronizer."""

from typing import TYPE_CHECKING, override

from dotenv import load_dotenv

from meta.clients.github_client import create_or_update_github_file
from meta.logger import print_section

from ._constants import LEADERSHIP
from .abstract import AbstractSynchronizer

if TYPE_CHECKING:
    from meta.models import Team


class CodeownersSynchronizer(AbstractSynchronizer):
    """Codeowners synchronizer."""

    GOLDADOR = "goldador"

    CODEOWNERS_FILE_PATH = ".github/CODEOWNERS"
    COMMIT_MESSAGE = "chore: auto-update CODEOWNERS"
    FILE_PATH = "meta/synchronizers/codeowners.py"

    def __init__(
        self,
    ) -> None:
        """Initialize the codeowners synchronizer."""
        super().__init__()

    @override
    def sync(self) -> None:
        print_section("Synchronizing CODEOWNERS file")
        create_or_update_github_file(
            self.CODEOWNERS_FILE_PATH,
            self.generate_codeowners_file(),
            self.COMMIT_MESSAGE,
        )

    def generate_codeowners_file(self) -> str:
        """Generate the CODEOWNERS file."""
        lines = [f"# Auto-generated CODEOWNERS file from {self.FILE_PATH}"]
        lines.append("")

        goldador_team = self.teams[self.GOLDADOR]
        lines.append("# Default owners are the Goldador team leads")
        lines.append(f"*{self._get_team_leads_pattern(goldador_team)}")
        lines.append("")

        leadership_team = self.teams[LEADERSHIP]
        lines.append(
            "# Owners of the `teams/` directory are the leadership team members",
        )
        lines.append(f"teams{self._get_team_members_pattern(leadership_team)}")
        lines.append("")

        lines.append(
            "# The codeowners of each team file are their corresponding leads",
        )
        lines.append("")
        for team_slug, team in sorted(self.teams.items()):
            codeowners_pattern = f"teams/{team_slug}.toml"
            codeowners_pattern += self._get_team_leads_pattern(team)
            lines.append(codeowners_pattern)
            lines.append("")

        return "\n".join(lines)

    def _get_team_leads_pattern(self, team: Team) -> str:
        """Get the codeowners pattern for the team's leads."""
        codeowners_pattern = ""
        for lead in sorted(team.leads):
            codeowners_pattern += f" @{lead}"
        return codeowners_pattern

    def _get_team_members_pattern(self, team: Team) -> str:
        """Get the codeowners pattern for the team's members."""
        codeowners_pattern = ""
        for member in sorted(team.members):
            codeowners_pattern += f" @{member}"
        return codeowners_pattern


def main() -> None:
    """CLI entry point."""
    load_dotenv()
    codeowners_synchronizer = CodeownersSynchronizer()
    codeowners_synchronizer.sync()
