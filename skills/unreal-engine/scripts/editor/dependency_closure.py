"""List every package a map pulls into the cook that lives outside the allowed roots.

Runs inside the Unreal Editor's Python: through an MCP Python tool, the Output
Log's Python console, or headless:

    python scripts/ue.py python --project ./MyGame \
        --script <skill>/scripts/editor/dependency_closure.py \
        --script-args /Game/MyGame/Maps/L_Main --allow /Game/MyGame

From an open editor's Python, import it and call closure() directly:

    closure(["/Game/MyGame/Maps/L_Main"], allow=["/Game/MyGame"])

Seeds are the map package plus the package of every loaded actor (One File Per
Actor levels keep each actor in its own package). For World Partition maps,
load all regions first or the result covers only loaded actors. Packages loaded
only by string at runtime are invisible here and to the cook.
"""

from __future__ import annotations

import sys

try:
    import unreal
except ImportError:  # imported outside the editor
    unreal = None

ALWAYS_ALLOWED = ("/Script/", "/Engine/", "/Memory/", "/Temp/")


def _deps(registry, package: str, options) -> list[str]:
    found = registry.get_dependencies(package, options) or []
    return [str(n) for n in found]


def _actor_packages(map_path: str) -> list[str]:
    unreal.EditorLoadingAndSavingUtils.load_map(map_path)
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    packages = set()
    for actor in subsystem.get_all_level_actors():
        try:
            packages.add(actor.get_outermost().get_name())
        except Exception:  # noqa: BLE001 - keep going on odd actors
            continue
    return sorted(packages)


def closure(maps: list[str], allow: list[str], include_engine: bool = False) -> list[str]:
    if unreal is None:
        raise RuntimeError("run this inside the Unreal Editor")
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    options = unreal.AssetRegistryDependencyOptions(
        include_soft_package_references=True,
        include_hard_package_references=True,
        include_searchable_names=False,
        include_soft_management_references=False,
        include_hard_management_references=False,
    )
    allowed = tuple(a.rstrip("/") + "/" for a in allow)
    skip = tuple(p for p in ALWAYS_ALLOWED if include_engine is False or p != "/Engine/")

    seen: set[str] = set()
    queue: list[str] = []
    for m in maps:
        queue.append(m)
        queue.extend(_actor_packages(m))
    while queue:
        pkg = queue.pop()
        if pkg in seen:
            continue
        seen.add(pkg)
        if pkg.startswith(skip):
            continue
        queue.extend(d for d in _deps(registry, pkg, options) if d not in seen)

    # External actor/object packages belong to their map; their own dependencies were followed.
    outside = sorted(p for p in seen
                     if p not in maps and not p.startswith(allowed) and not p.startswith(skip)
                     and "/__ExternalActors__/" not in p and "/__ExternalObjects__/" not in p)
    unreal.log(f"dependency_closure: {len(seen)} packages reached from {len(maps)} map(s)")
    if outside:
        unreal.log_warning(f"dependency_closure: {len(outside)} package(s) outside {list(allow)}:")
        for p in outside:
            unreal.log_warning(f"  OUTSIDE {p}")
    else:
        unreal.log("dependency_closure: 0 outside")
    return outside


def _parse(argv: list[str]) -> tuple[list[str], list[str], bool]:
    maps, allow, include_engine, mode = [], [], False, "maps"
    for arg in argv:
        if arg == "--allow":
            mode = "allow"
        elif arg == "--include-engine":
            include_engine = True
        elif mode == "allow":
            allow.append(arg)
        else:
            maps.append(arg)
    return maps, allow, include_engine


if __name__ == "__main__" and unreal is not None:
    _maps, _allow, _engine = _parse(sys.argv[1:])
    if not _maps or not _allow:
        unreal.log_warning("usage: dependency_closure.py <map> [<map> ...] --allow </Game/Root> [...] "
                           "[--include-engine]")
    else:
        closure(_maps, _allow, _engine)
