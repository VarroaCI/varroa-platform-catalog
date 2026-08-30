#!/usr/bin/env python3
"""Validate catalog.yaml and the content files it indexes.

Mirrors the checks the Varroa operator applies at CatalogSource sync time
(bundle.ValidateCatalogItem), plus repo-level invariants the operator cannot
see: duplicate names, unindexed content files, and plugin pins drifting from
the version-profile lock snapshot under locks/.
"""

import pathlib
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
VALID_TYPES = {"podtemplate", "plugin", "item", "jcasc", "rbac", "pipeline-template"}
CONTENT_DIRS = {
    "pod-templates": "podtemplate",
    "plugins": "plugin",
    "items": "item",
    "jcasc": "jcasc",
}
RBAC_KINDS = {"JenkinsRole", "JenkinsRoleBinding"}

errors = []


def err(msg: str) -> None:
    errors.append(msg)


def load_yaml(path: pathlib.Path):
    try:
        return yaml.safe_load(path.read_text())
    except yaml.YAMLError as e:
        err(f"{path.relative_to(ROOT)}: YAML parse error: {e}")
        return None


def check_entry_content(entry: dict, doc) -> None:
    typ, path = entry["type"], entry["path"]
    if doc is None:
        err(f"{path}: empty or unparseable content")
        return
    if typ == "plugin":
        plugins = doc.get("plugins") if isinstance(doc, dict) else None
        if not isinstance(plugins, list) or not plugins:
            err(f"{path}: plugin content needs a non-empty 'plugins' list")
            return
        for i, p in enumerate(plugins):
            if not isinstance(p, dict) or not p.get("artifactId"):
                err(f"{path}: plugins[{i}]: artifactId is required")
            elif not p.get("version"):
                err(f"{path}: plugins[{i}] ({p['artifactId']}): version is required")
    elif typ in ("item", "pipeline-template"):
        items = doc.get("items") if isinstance(doc, dict) else None
        if not isinstance(items, list) or not items:
            err(f"{path}: item content needs a non-empty 'items' list")
    elif typ == "jcasc":
        if not isinstance(doc, dict) or not doc:
            err(f"{path}: jcasc content must be a non-empty YAML map")
    elif typ == "rbac":
        roles = doc.get("roles") if isinstance(doc, dict) else None
        if not isinstance(roles, dict) or not roles:
            err(f"{path}: rbac content needs a non-empty 'roles' map")
    elif typ == "podtemplate":
        if not isinstance(doc, list) or not doc:
            err(f"{path}: podtemplate content must be a non-empty YAML list")


def check_variables(entry: dict) -> None:
    variables = entry.get("variables", [])
    if not isinstance(variables, list):
        err(f"catalog.yaml: {entry.get('name')}: variables must be a list")
        return
    for v in variables:
        if not isinstance(v, dict) or not v.get("name"):
            err(f"catalog.yaml: {entry.get('name')}: every variable needs a name")


def main() -> int:
    index = load_yaml(ROOT / "catalog.yaml")
    if not isinstance(index, dict) or not isinstance(index.get("items"), list):
        err("catalog.yaml: missing or invalid 'items' list")
        print("\n".join(errors))
        return 1

    names, paths = set(), set()
    plugin_pins = {}  # artifactId -> (version, path)

    for entry in index["items"]:
        name, typ, path = entry.get("name"), entry.get("type"), entry.get("path")
        if not name or not typ or not path:
            err(f"catalog.yaml: entry {entry}: name, type, and path are all required")
            continue
        if typ not in VALID_TYPES:
            err(f"catalog.yaml: {name}: invalid type {typ!r}")
        if name in names:
            err(f"catalog.yaml: duplicate name {name!r}")
        if path in paths:
            err(f"catalog.yaml: duplicate path {path!r}")
        names.add(name)
        paths.add(path)
        check_variables(entry)

        file = ROOT / path
        if ".." in path or path.startswith("/"):
            err(f"catalog.yaml: {name}: unsafe path {path!r}")
            continue
        if not file.is_file():
            err(f"catalog.yaml: {name}: path {path} does not exist")
            continue
        doc = load_yaml(file)
        check_entry_content(entry, doc)

        if typ == "plugin" and isinstance(doc, dict):
            for p in doc.get("plugins") or []:
                if isinstance(p, dict) and p.get("artifactId"):
                    aid, ver = p["artifactId"], str(p.get("version", ""))
                    if aid in plugin_pins and plugin_pins[aid][0] != ver:
                        err(
                            f"{path}: {aid} pinned to {ver} but "
                            f"{plugin_pins[aid][1]} pins {plugin_pins[aid][0]}"
                        )
                    plugin_pins[aid] = (ver, path)

    # Unindexed YAML in a content dir is silently ignored by the operator —
    # here that is always a mistake.
    for dirname in CONTENT_DIRS:
        for f in sorted((ROOT / dirname).glob("*.y*ml")):
            rel = str(f.relative_to(ROOT))
            if rel not in paths:
                err(f"{rel}: not indexed in catalog.yaml (the operator would ignore it)")

    # Plugin pins that overlap a lock snapshot must match it exactly.
    for lock_file in sorted((ROOT / "locks").glob("*.yaml")):
        lock = load_yaml(lock_file)
        locked = lock.get("plugins", {}) if isinstance(lock, dict) else {}
        for aid, (ver, path) in sorted(plugin_pins.items()):
            if aid in locked and str(locked[aid]) != ver:
                err(
                    f"{path}: {aid} pinned to {ver} but {lock_file.name} "
                    f"locks {locked[aid]} — controllers would wedge with a plugin version conflict"
                )

    # RBAC manifests are CRD documents, not catalog content.
    for f in sorted((ROOT / "rbac").glob("*.yaml")):
        for doc in yaml.safe_load_all(f.read_text()):
            if doc is None:
                continue
            rel = str(f.relative_to(ROOT))
            kind = doc.get("kind")
            if kind not in RBAC_KINDS:
                err(f"{rel}: unexpected kind {kind!r} (want JenkinsRole or JenkinsRoleBinding)")
                continue
            spec = doc.get("spec") or {}
            if not (doc.get("metadata") or {}).get("name"):
                err(f"{rel}: {kind} missing metadata.name")
            if kind == "JenkinsRole" and not spec.get("permissions"):
                err(f"{rel}: JenkinsRole {doc['metadata']['name']}: permissions are required")
            if kind == "JenkinsRoleBinding":
                if not spec.get("roleRef"):
                    err(f"{rel}: JenkinsRoleBinding {doc['metadata']['name']}: roleRef is required")
                if not spec.get("subjects"):
                    err(f"{rel}: JenkinsRoleBinding {doc['metadata']['name']}: subjects are required")

    if errors:
        print(f"FAIL: {len(errors)} problem(s)")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"OK: {len(names)} catalog entries validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
