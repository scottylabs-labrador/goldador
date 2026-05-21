# 7. validator as a service

Date: 2026-05-16

## Status

Accepted

## Context

When a forked PR is created in GitHub, the pull request doesn't have access to
the repository's secrets. However, the validator needs acccesses such as Keycloak
and GitHub API tokens to perform the validation.

## Decision

We are going to deploy the validator as a service at goldador.scottylabs.org.
It will take in a GitHub ref as input and return the validation results.

### Alternative 1: Use pull_request_target

The `pull_request_target` event will allow the validator to access the repository's
secrets. However, it is easy to result in security vulnerabilities and is not
recommended by the GitHub security team. It is in fact the root cause of the recent
[TanStack npm Compromise](https://tanstack.com/blog/incident-followup#the-honest-part).

### Alternative 2: Use workflow_run

We can use the `workflow_run` event to trigger the validator on the main branch
when a PR is created. However, this will not be automatically be attached to the
PR as a CI check.

## Consequences

We are going to deploy the validator as a service at goldador.scottylabs.org.
This involves rewriting the validator to be a Python server.
