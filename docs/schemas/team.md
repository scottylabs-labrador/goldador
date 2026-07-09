# Adding a team

> [!NOTE]
> This is for team leads seeking to register their team.

Choose a team slug. The team slug is used to identify the team internally
(e.g. Slack channel name). It should be a short, lowercase, and hyphen-separated
string. Create a new TOML file in `teams/` with the team slug as the filename:

```toml
# The name is used to identify the team publicly (e.g. GitHub org team name).
name = "Your Team Name"

description = """
A brief description of the team.
"""

# The website and server are not required until the team is ready to deploy.
# Omit the https:// prefix for the website and server.
website = "your-team-website.com"
server = "your-team-server.com"

# Set the `create-oidc-clients` field to `false` if the team does not need OIDC
# clients. OIDC clients are necessary if you want to use ScottyLabs' auth system!
#
# It defaults to true if not specified, so please remove this section if the team
# DO need OIDC clients.
create-oidc-clients = false

# List of repositories owned by the team.
# Note that the owners of the repositories must be ScottyLabs-Labrador.
[[repos]]
name = "repo-name-1" # As it appears at the end of the GitHub repository URL
description = "A brief description of repo 1."

[[repos]]
name = "repo-name-2" # As it appears at the end of the GitHub repository URL
description = "A brief description of repo 2."

# List of membership records by timeframe.
# Note that only the first record will be used for synchronization.
[[membership]]

# The timeframe can be any string, but we suggest using either the year or semester.
# E.g. "2026-2027" or "Spring 2026".
timeframe = "timeframe-1"

# List of the GitHub usernames of the leads for this timeframe.
leads = ["lead-1", "lead-2"]

# List of members for this timeframe.
[[membership.members]]
github-username = "member-1"
title = "Member 1's title" # The title is optional.

[[membership.members]]
github-username = "member-2"
title = "Member 2's title"
```

Visit the [team schema](../../meta/schemas/team.schema.json) to learn more about
each field.
