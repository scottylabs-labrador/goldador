# 6. decide google sync strategies

Date: 2026-05-07

## Status

Accepted

## Context

We want to synchronize Google Group and Google Drive permissions within Labrador.

## Decision

### Google Group

We will use OpenTofu to synchronize Google Group permissions since it is declarative
and easy to manage. It is the default synchronization strategy we use.

### Google Drive

We will use Python scripts to synchronize Google Drive permissions due to the following reasons:

1. Many Labrador members are already added to Google Drive and importing/removing
   them manually is time-consuming and non-ideal. This could also be a problem
   in a future since people are very used to adding members direclty to Google Drive.

2. Role-wise, some Labrador leadership are Content Managers while others are Managers,
   making it difficult to manage with OpenTofu.

## Consequences

Going forward, we will use OpenTofu to synchronize Google Group permissions
and Python scripts to synchronize Google Drive permissions.
