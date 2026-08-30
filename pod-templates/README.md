# Pod templates

Each file is a single-element YAML list in the
[kubernetes-plugin](https://plugins.jenkins.io/kubernetes/) pod template
schema. At compose time the operator injects these under
`jenkins.clouds[].kubernetes.templates`, so a bundle using them also needs a
cloud definition — compose the `k8s-cloud` JCasC item alongside.

Conventions used here:

- **Keep the container alive.** Most tool images exit immediately without a
  command, which makes the agent pod die before the build starts. Templates
  set `command: sleep` / `args: 99d` (busybox-style images use their own
  idiom, see `kaniko.yaml`).
- **Request real resources.** Every container declares requests and limits
  sized for the toolchain; bump them in your own copy rather than deleting
  them.
- **Cache what the toolchain caches.** Dependency caches (`.m2`, `/go/pkg/mod`,
  cargo registry, NuGet, `.gradle`) are `emptyDirVolume` mounts so warm pods
  (`idleMinutes: 5`) reuse downloads within their idle window.
- **Privileged pods don't linger.** `dind` uses `podRetention: never` and no
  idle reuse.
- **No secrets in templates.** Cloud agents (aws-cli, gcloud, azure-cli,
  ansible) authenticate through pod identity (IRSA / workload identity) or
  Jenkins credentials injected by the pipeline — see each file's header
  comment.

Every template has a matching runnable smoke item under `items/` that proves
the agent schedules and the toolchain works.
