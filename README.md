# Varroa Platform Catalog

Curated catalog for [Varroa](https://github.com/varroaci/varroa-jenkins):
pod templates, plugin sets, job definitions, and JCasC fragments that
compose into production Jenkins controllers. Everything here is meant to be
used as-is or copied as a starting point for your own catalog.

## Layout

```
catalog.yaml          the index — every entry the operator syncs
pod-templates/        Kubernetes agent pod definitions (languages + cloud tooling)
plugins/              pinned Jenkins plugin sets
items/                job and folder definitions, including runnable CI smokes
jcasc/                configuration-as-code fragments
rbac/                 JenkinsRole/JenkinsRoleBinding manifests (kubectl-applied, not catalog items)
pipeline-library/     the varroa-shared global pipeline library
locks/                plugin-version lock snapshots that CI checks pins against
examples/             sample ComposedBundle wiring
```

Each directory has its own README with the file format and conventions.

## How it works

1. A `CatalogSource` points the Varroa operator at this repository.
2. The operator parses `catalog.yaml` and creates a `CatalogItem` CRD per entry.
3. Items are assembled into a `ComposedBundle`, in the UI or by hand.
4. A `Controller` references the bundle via `spec.composedBundleRef`, and the
   operator pushes the composed configuration to that Jenkins instance.

Register the catalog:

```yaml
apiVersion: varroa.dev/v1alpha1
kind: CatalogSource
metadata:
  name: platform-catalog
  namespace: varroa-system
spec:
  repoURL: https://github.com/varroaci/varroa-platform-catalog.git
  revision: main
  syncIntervalSeconds: 300
  trusted: true
```

## The index

Every entry in `catalog.yaml` declares:

| Field | Meaning |
|---|---|
| `type` | `podtemplate`, `plugin`, `item`, `jcasc`, `rbac`, or `pipeline-template` |
| `name` | unique identifier; the CatalogItem CRD is named `<source>-<slugified-path>` |
| `displayName`, `description`, `tags` | what the UI shows and filters on |
| `path` | file within this repo |
| `version` | change marker (`bundle` for plugin sets — the real pins live in the file) |
| `variables` | user-supplied parameters, `${name}` placeholders in the content |

Without a `catalog.yaml` the operator falls back to scanning the directory
convention, but this repo always ships an explicit index.

## Composition rules worth knowing

- `jcasc` fragments deep-merge in input order. Duplicate keys follow the
  bundle's `jcascMergeStrategy`: `errorOnConflict` (default) or `override`.
- `podtemplate` entries are injected under `jenkins.clouds[].kubernetes.templates`
  of the merged JCasC, so compose the `k8s-cloud` item (or your own cloud
  fragment) alongside them.
- `plugin` entries are deduplicated by `artifactId`; a version that also
  appears in the platform's `JenkinsVersionProfile` lock must match it
  exactly, or the operator refuses to reconcile the controller. The pinned
  snapshot lives in `locks/` and CI enforces agreement.
- Variables resolve item defaults first, then bundle-wide `spec.variables`,
  then per-input overrides. The operator injects `${varroa_controller_name}`,
  `${varroa_controller_namespace}`, `${varroa_controller_endpoint}`, and the
  `${varroa_oidc_*}` set automatically.
- Authorization is the one thing bundles do not carry: Varroa strips
  `authorizationStrategy` from JCasC and builds the role-strategy
  configuration from `JenkinsRole`/`JenkinsRoleBinding` CRDs instead. The
  manifests in `rbac/` are applied with kubectl, not composed into bundles.

## Contributing

Add the file, index it in `catalog.yaml`, and bump the entry's `version` when
you change existing content. CI validates the index, per-type file shapes,
and plugin pins on every pull request. Merged changes reach registered
clusters on the next sync interval.

## License

MIT — see [LICENSE](LICENSE). The Varroa operator itself is licensed
separately; see its repository.
