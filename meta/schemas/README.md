# Schemas

This directory contains the JSON schemas for the TOML files in the `members/`
and `teams/` directories.

## Files

- [`member.schema.json`](member.schema.json) validates files in
  [`members/`](../../members/). A member file must include `full-name` and may
  include `andrew-id`.
- [`team.schema.json`](team.schema.json) validates files in
  [`teams/`](../../teams/). A team file declares display metadata, repositories,
  and membership records.

Taplo reads these schemas through [`../../.taplo.toml`](../../.taplo.toml), so
editor diagnostics and CI validation use the same schema files.

## Key Ordering

The Python loader also uses the order of each schema's top-level `properties`
object as the required TOML key order. When adding or reordering schema fields,
update example TOML and schema documentation at the same time so generated
validation messages remain clear.

## Documentation

See the [schemas documentation directory](../../docs/schemas/) for author-facing
examples:

- [`member.md`](../../docs/schemas/member.md)
- [`team.md`](../../docs/schemas/team.md)

## Troubleshooting

If you are using the VSCode extension [tamasfe.even-better-toml](https://marketplace.visualstudio.com/items?itemName=tamasfe.even-better-toml), you most likely need to clear the cache to see the changes after updating a schema.

Run the following command to find the cache directory:

```zsh
find ~ -type d -name "tamasfe.even-better-toml"
```

After you delete the cache directory and reload VSCode (or restart the extension),
the extension should start using the updated schemas.
