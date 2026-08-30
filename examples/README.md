# Examples

Sample wiring that shows how catalog items become a running configuration.

- `varroa-themed-bundle.yaml` — a minimal `ComposedBundle` combining one
  plugin set and one JCasC fragment (the Varroa UI theme). The pattern
  generalizes: list `itemRef` inputs in merge order, pick a
  `jcascMergeStrategy`, and point a `Controller`'s `composedBundleRef` at the
  result.

CatalogItem CRD names follow `<CatalogSource-name>-<slugified-path>` — e.g. a
source named `platform-catalog` exposes `jcasc/varroa-theme.yaml` as
`platform-catalog-jcasc-varroa-theme`.
