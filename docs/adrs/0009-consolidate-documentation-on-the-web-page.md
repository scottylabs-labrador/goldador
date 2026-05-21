# 9. consolidate documentation on the web page

Date: 2026-05-16

## Status

Accepted

## Context

[ADR 8](0008-decide-wiki-and-web-documentation-boundaries.md) split Goldador's
user-facing documentation between `web/index.html` for the public permission guide
and the GitHub Wiki for setup, validation, and pull request process guidance.

That boundary reduces duplication only if maintainers consistently decide which
surface owns each change. In practice, Goldador's documentation is expected to be
maintained by only a few people, and possibly just one person, so the collaborative
editing affordances of the GitHub Wiki are less important than keeping the
documentation system simple.

Keeping all user-facing documentation in `web/index.html` also collocates the
source for the published documentation with the rest of the GitHub repository.
This makes documentation changes reviewable through the same pull request process
as code and avoids maintaining a separate GitHub Wiki surface.

## Decision

We will delete the GitHub Wiki and use `web/index.html` as the only maintained
user-facing documentation surface for Goldador.

`web/index.html` owns the permission guide, setup and registration steps,
validation requirements, and pull request review and merge process documentation.
References that previously pointed readers to the Goldador Wiki should instead
point to the published web page backed by `web/index.html`.

### Alternative 1: Keep the GitHub Wiki for collaborative editing

GitHub Wiki pages are useful when many contributors need a low-friction way to
edit documentation outside the normal repository workflow. Goldador does not
currently need that tradeoff because its documentation is maintained by a small
group, so a separate wiki adds more complexity than collaboration value.

## Consequences

Future user-facing documentation changes update `web/index.html` first.

Maintainers no longer need to decide whether a user-facing documentation change
belongs on the web page or in the wiki. There is one canonical place to update,
review, and publish Goldador documentation.

Existing links or text that send users to the GitHub Wiki should be removed or
changed to point to the published web page.
