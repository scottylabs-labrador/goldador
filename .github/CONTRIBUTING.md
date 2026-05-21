# Contributing to Goldador

For prerequisites, fork setup, and registration steps, see the
[Register or Update Access](https://scottylabs-labrador.github.io/goldador/#register)
section of the public guide. This file covers submitting and reviewing pull
requests against the Goldador repository.

## Editor Setup

Install the recommended VS Code extensions so TOML files auto-format on save.

- Use the Command Palette (Command+Shift+P) and search for
  "Extensions: Show Recommended Extensions" to show the recommended extensions.

- See the "Installing recommended extensions" section in
  [this article](https://dev.to/askrishnapravin/recommend-vs-code-extensions-to-your-future-teammates-4gkb)
  for a GIF showing how to install recommended extensions.

- See the
  [VS Code Extensions documentation](https://code.visualstudio.com/docs/configure/extensions/extension-marketplace#_recommended-extensions)
  for more details.

## Submit a PR

Commit your changes, push to your fork, and open a pull request against the
`main` branch of `scottylabs-labrador/goldador`.

Two hard CI rules apply to every PR:

- Submit the PR from your own GitHub account. PRs that add a member on behalf
  of someone else are automatically rejected.

- Make one change per PR: add yourself as a member, or join/create one team —
  not both in the same PR. PRs that change more than one file in `members/` or
  `teams/` are automatically rejected.

## PR Review Process

### Request Reviewers

Reviewers are automatically requested according to the
[CODEOWNERS file](https://github.com/scottylabs-labrador/goldador/blob/main/.github/CODEOWNERS).

### CI Checks

A reviewer will approve the CI checks to run after verifying that the PR
contains no malicious code. All CI checks must pass before the PR can be
merged. See the
[Validator README](https://github.com/scottylabs-labrador/goldador/tree/main/meta/validator)
for what is validated and how to run some checks locally to speed up review.

### Draft PR

The reviewer will convert the PR to a
[draft PR](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests#draft-pull-requests)
if it is not ready to be merged, and may leave comments outlining required
changes. It is the member's responsibility to address and resolve these
comments before the PR can proceed.

When the PR is ready, the member should
[mark the PR as ready for review](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/changing-the-stage-of-a-pull-request#marking-a-pull-request-as-ready-for-review)
and ensure the branch is
[up to date with `main`](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/keeping-your-pull-request-in-sync-with-the-base-branch#updating-your-pull-request-branch).
Since the reviewer will squash-merge the PR, the member may either rebase
their branch or merge `main` into it.

Marking the PR as ready for review notifies the reviewers automatically, so
the member does not need to ping them unless there is no response after a few
days. This cycle may repeat until the PR is ready to be merged.

### PR Merging

All PRs are squash-merged to maintain a clean and readable commit history.
Example squash titles:

- `feat(member): add Yuxiang to leadership team (#PR)`
- `feat(team): update description of leadership team (#PR)`

Rationale: a new member or team joining ScottyLabs is a feature, not a chore.

The pull request number (e.g. `(#123)`) is automatically appended to the title
when the PR is squash-merged by the reviewer, so contributors do not need to
include `(#PR)` literally in their PR title.
