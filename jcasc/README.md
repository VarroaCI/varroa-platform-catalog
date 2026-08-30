# JCasC fragments

Raw [configuration-as-code](https://plugins.jenkins.io/configuration-as-code/)
YAML, deep-merged in input order when a bundle composes several fragments.
Duplicate scalar keys follow the bundle's `jcascMergeStrategy`:
`errorOnConflict` (default) fails naming the key, `override` lets the later
fragment win. Lists are replaced wholesale, not merged — which is why pod
templates are their own item type rather than JCasC fragments.

Notes on specific fragments:

- `k8s-cloud.yaml` — the in-cluster agent cloud. Uses the operator-injected
  `${varroa_controller_namespace}` and `${varroa_controller_endpoint}`
  variables, so it works unmodified for every controller.
- `global-tools.yaml` — tool installers (`maven3`, `jdk21`, `node20`, git)
  plus a managed empty Maven settings file. The `maven-ci` item depends on
  the `maven3` installer; the toolchain plugins come from the `cicd-tools`
  plugin set.
- `seed-jobs.yaml` — seeds jobs through the JCasC `jobs:` root (job-dsl).
  Runs as SYSTEM at configuration-apply time.
- `shared-library.yaml` — registers `varroa-shared` from this repo's
  `pipeline-library/` directory.
- Do not add `jenkins.authorizationStrategy` here: Varroa owns authorization
  and strips that key from every bundle. Use the CRD manifests in
  [`rbac/`](../rbac/) instead. Security realm configuration is likewise
  operator-owned.
