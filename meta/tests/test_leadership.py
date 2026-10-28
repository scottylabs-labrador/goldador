"""Test setting Labrador's leadership from Grouper."""

from meta.models import Member, Team
from meta.synchronizers.src.leadership import (
    LABRADOR_ROLES,
    set_leadership_from_grouper,
)


def _member(andrew_id: str | None) -> Member:
    return Member.model_validate(
        {"full-name": "Test Member", "andrew-id": andrew_id, "file_path": "test.toml"},
    )


def _leadership(leads: list[str], members: list[str]) -> Team:
    return Team(
        file_path="teams/leadership.toml",
        name="Leadership",
        description="Test leadership",
        repos=[],
        leads=leads,
        members=members,
    )


GROUPS = {
    f"{LABRADOR_ROLES}:all": {"hbenko", "yh4", "laki", "nofile"},
    f"{LABRADOR_ROLES}:director": {"hbenko"},
    f"{LABRADOR_ROLES}:head-of-onboarding-and-documentation": {"yh4"},
}

MEMBERS = {
    "hanabenko": _member("HBenko"),
    "Yuxiang-Huang": _member("yh4"),
    "laasyaaki": _member("laki"),
    "jagong-cmu": _member("jagong"),
    "no-andrew-id": _member(None),
}


def test_sets_role_holders_and_lead_roles() -> None:
    """Role holders become members, and lead role holders become leads."""
    leadership = _leadership(leads=[], members=[])
    set_leadership_from_grouper(leadership, MEMBERS, GROUPS.__getitem__)
    assert leadership.members == ["Yuxiang-Huang", "hanabenko", "laasyaaki"]
    assert leadership.leads == ["Yuxiang-Huang", "hanabenko"]


def test_skips_role_holders_without_member_files() -> None:
    """A role holder with no member file can't be mapped to a GitHub username."""
    leadership = _leadership(leads=[], members=[])
    set_leadership_from_grouper(leadership, MEMBERS, GROUPS.__getitem__)
    assert "nofile" not in leadership.members
