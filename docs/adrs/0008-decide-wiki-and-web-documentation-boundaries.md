# 8. decide wiki and web documentation boundaries

Date: 2026-05-16

## Status

Superseded by [9. consolidate documentation on the web page](0009-consolidate-documentation-on-the-web-page.md)

## Context

Goldador has two user-facing documentation surfaces for Labrador members: the
public web page at `web/index.html`, published at
<https://scottylabs-labrador.github.io/goldador/>, and the GitHub wiki home page
at `wiki/Home.md`, published at
<https://github.com/scottylabs-labrador/goldador/wiki>.

Both pages help members understand how to get the permissions they need, but
duplicating role permissions, setup steps, validations, and pull request process
details across both pages causes drift and makes future documentation changes
harder to place.

## Decision

We will use `web/index.html` as the canonical public permission guide for
Goldador. It owns role cards, service links, and stable descriptions of what
access each Labrador role receives.

We will use `wiki/Home.md` as the canonical setup and contribution guide. It
owns prerequisites, registration steps, validation requirements, and pull request
review and merge process documentation.

Either page may include short summaries and cross-links to the other page, but
the full permission guide belongs on the web page and the full setup and
workflow guide belongs on the wiki. Technical implementation details should stay
out of both user-facing surfaces unless a user needs them to complete an action.

## Consequences

Future permission changes update `web/index.html` first, with any wiki mention
kept brief and linked back to the public permission guide.

Future setup, validation, or pull request process changes update `wiki/Home.md`
first, with any web mention kept brief and linked back to the wiki.

Maintainers should choose the documentation surface based on this boundary before
adding or moving Goldador user-facing content.
