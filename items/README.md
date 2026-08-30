# Items

Job and folder definitions in Varroa's items schema: an `items:` list where
each element has a `kind` (`pipeline`, `folder`, `multibranch`, `freeStyle`),
a `name`, and kind-specific fields. Pipelines embed their Jenkinsfile as
`definition.script`.

Two families live here:

- **Scaffolds** (`multibranch.yaml`, `team-folder.yaml`) are parameterized
  with `${...}` variables you fill in when composing — repo, org, team name.
- **CI smokes** (`*-ci.yaml`, `terraform-validate.yaml`, `helm-render.yaml`,
  `dind-smoke.yaml`) are deliberately self-contained: each scaffolds its own
  fixture in the workspace and runs green with no external repositories and
  no credentials. They exist to prove an agent template works end-to-end and
  to serve as copy-paste starting points. Some need outbound network for
  dependency downloads (noted per item); none need secrets.

Keep `${...}` out of pipeline scripts unless it is a declared catalog
variable — the composer resolves `${name}` placeholders at compose time, and
an unresolved one fails the bundle's completeness check. In Groovy, prefer
string concatenation or `format()`-style construction over `${}` interpolation
for anything that is not a catalog variable.
