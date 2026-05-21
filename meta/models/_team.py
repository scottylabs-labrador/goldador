from pydantic import BaseModel


class Team(BaseModel):
    """Team record loaded from `teams/*.toml`."""

    file_path: str
    name: str
    description: str
    website: str | None = None
    server: str | None = None
    create_oidc_clients: bool = True
    repos: list[Repo]
    leads: list[str]
    members: list[str]


class Repo(BaseModel):
    """Repository record loaded from `teams/*.toml`."""

    name: str
    description: str
