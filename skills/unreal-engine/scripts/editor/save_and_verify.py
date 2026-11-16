"""Save every dirty package, then report anything still unsaved.

Runs inside the Unreal Editor's Python (MCP Python tool or the Python console):

    exec(open(r"<skill>/scripts/editor/save_and_verify.py").read())

or import it and call save_and_verify(). Use it before closing the editor,
before handing it to another agent, and after any scripted edit. Then confirm
on disk: changed actors in One File Per Actor levels appear as changed files
under Content/__ExternalActors__/ in `git status`.

To make a scripted actor edit persist, mark the actor first:

    with unreal.ScopedEditorTransaction("Move spawn"):
        actor.modify()
        actor.set_actor_location(unreal.Vector(-120, 330, 100), False, False)
"""

from __future__ import annotations

try:
    import unreal
except ImportError:  # imported outside the editor
    unreal = None


def _dirty() -> tuple[list[str], list[str]]:
    utils = unreal.EditorLoadingAndSavingUtils
    maps, content = [], []
    if hasattr(utils, "get_dirty_map_packages"):
        maps = [p.get_name() for p in (utils.get_dirty_map_packages() or [])]
    if hasattr(utils, "get_dirty_content_packages"):
        content = [p.get_name() for p in (utils.get_dirty_content_packages() or [])]
    return maps, content


def save_and_verify() -> bool:
    if unreal is None:
        raise RuntimeError("run this inside the Unreal Editor")
    before_maps, before_content = _dirty()
    unreal.log(f"save_and_verify: dirty before: {len(before_maps)} map, {len(before_content)} content")
    for name in before_maps + before_content:
        unreal.log(f"  dirty {name}")

    ok = unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)

    after_maps, after_content = _dirty()
    left = after_maps + after_content
    if left:
        unreal.log_warning(f"save_and_verify: {len(left)} package(s) still dirty after saving:")
        for name in left:
            unreal.log_warning(f"  STILL DIRTY {name}")
    if not hasattr(unreal.EditorLoadingAndSavingUtils, "get_dirty_map_packages"):
        unreal.log_warning("save_and_verify: this engine cannot list dirty packages from Python; "
                           "check the editor's unsaved count and git status instead")
    result = bool(ok) and not left
    unreal.log(f"save_and_verify: {'OK' if result else 'NOT OK'}")
    return result


if __name__ == "__main__" and unreal is not None:
    save_and_verify()
