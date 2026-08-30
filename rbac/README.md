# RBAC cookie cutters

Ready-to-apply `JenkinsRole` + `JenkinsRoleBinding` manifests for the access
patterns most organizations need:

| File | Pattern |
|---|---|
| `standard-ladder.yaml` | admin / release-manager / developer / viewer tiers bound to directory groups |
| `auditor-security.yaml` | read-only compliance auditor + security officer with credential-inventory visibility |
| `contractor.yaml` | external collaborators fenced to one folder subtree |

These are Kubernetes CRDs, not catalog items:

```bash
kubectl apply -f rbac/standard-ladder.yaml
```

Varroa builds each controller's role-strategy configuration from these
resources. It deliberately ignores authorization content inside JCasC bundles
(`authorizationStrategy` is stripped), so CRDs are the only path that works —
and the reason this directory is not indexed in `catalog.yaml`.

Adapting the snippets:

- **Group names** under `subjects` must match what your identity provider
  emits. Edit them; everything else can usually stay.
- **Permissions** use dotted Jenkins IDs (`hudson.model.Item.Build`). Stick to
  the Overall / Job / Run / View / Agent / SCM / Credentials groups —
  role-strategy silently drops IDs it cannot resolve.
- **`jenkinsScope`** limits where an `Item` role applies: `Folder` with
  `propagate: Subtree` fences a subtree, `Pattern` matches a regex over full
  item names. Omit it for global bindings.
- **`controllerScope`** (namespaces or a label selector) limits which
  controllers a binding reaches — useful when one cluster hosts several
  teams' controllers.

Varroa also reconciles built-in roles (`varroa-admin`, `varroa-operator`,
`varroa-developer`, `varroa-viewer`). Create new roles alongside them rather
than editing the built-ins.

Connected controllers pick up role changes without reprovisioning.
