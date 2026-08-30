# Varroa Platform Catalog

Blessed platform catalog for [Varroa](https://github.com/varroaci/varroa-jenkins) — JCasC templates, plugins, pod templates, Jobs, and RBAC curated for production Jenkins controllers.

## Structure

```
varroa-platform-catalog/
├── catalog.yaml          ← explicit index (preferred over directory convention)
├── pod-templates/        ← Jenkins k8s plugin pod templates
├── plugins/              ← Jenkins plugin sets (artifactId + version)
├── items/                ← Jenkins job/folder definitions
├── jcasc/                ← JCasC configuration fragments
└── rbac/                 ← Role-Based Access Control role sets
```

## How It Works

1. A `CatalogSource` CRD points at this repo.
2. The Varroa operator clones it, parses `catalog.yaml`, and creates a `CatalogItem` CRD for each entry.
3. Users browse items in the Varroa UI and assemble them into a `ComposedBundle`.
4. The `ComposedBundle` is attached to a `Controller` via `composedBundleRef`.
5. The operator composes all items into a unified JCasC bundle and pushes it to the Jenkins controller.

## Catalog Index (`catalog.yaml`)

The `catalog.yaml` file is the explicit index. Each entry declares:
- `type` — one of `podtemplate`, `plugin`, `item`, `jcasc`, `rbac`
- `name` — unique identifier (referenced by `ComposedBundle`)
- `displayName` — human-readable title
- `description` — short summary
- `path` — relative file path within the repo
- `tags` — search/filter labels
- `variables` — user-configurable parameters with defaults

If `catalog.yaml` is absent, the operator falls back to scanning the directory convention (`pod-templates/` → `podtemplate`, etc.).

## Item Types

| Type | Purpose | Output |
|------|---------|--------|
| `podtemplate` | Kubernetes pod agent definitions | Wrapped under `jenkins.clouds[].kubernetes.templates` |
| `plugin` | Jenkins plugin sets | Deduplicated by `artifactId`, appended to `plugins.yaml` |
| `item` | Job and folder definitions | Concatenated into `items.yaml` |
| `jcasc` | JCasC configuration fragments | Merged into `jenkins.yaml` |
| `rbac` | Role-based access control definitions | Merged into `rbac.yaml` |

## Variable Resolution

Catalog items can declare variables with defaults. At compose time, variables resolve with this precedence (lowest to highest):

1. Item defaults (`CatalogItem.Spec.Variables[].Default`)
2. Composition-wide variables (`ComposedBundle.Spec.Variables`)
3. Per-item ref variables (`ComposedItemRef.Variables`)
4. Auto-vars injected by the operator:
   - `${varroa_controller_name}`
   - `${varroa_controller_namespace}`
   - `${varroa_controller_endpoint}`
   - `${varroa_oidc_issuer}`
   - `${varroa_oidc_client_id}`
   - `${varroa_oidc_client_secret}`

## JCasC Merge Strategy

When multiple `jcasc` items are composed, duplicate top-level keys are handled by the merge strategy set on the `ComposedBundle`:

- `errorOnConflict` (default) — fails with an error naming the conflicting key
- `override` — last item wins

## Registering This Catalog

```yaml
apiVersion: varroa.dev/v1alpha1
kind: CatalogSource
metadata:
  name: platform-catalog
  namespace: varroa-system
spec:
  repoURL: https://github.com/varroaci/varroa-platform-catalog.git
  revision: master
  syncIntervalSeconds: 300
  trusted: true
```

```bash
kubectl apply -f catalog-source.yaml
```

After registration, the operator will clone the repository, create `CatalogItem` CRDs for each entry, and keep them in sync on a 300-second interval (or on-demand via `:sync`).

## Contributing

1. Add the YAML file(s) in the appropriate directory.
2. Add an entry to `catalog.yaml`.
3. Open a PR. Merged changes are picked up on the next sync cycle.

## License

MIT — see the Varroa project for details.
