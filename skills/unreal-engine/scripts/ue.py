#!/usr/bin/env python3
"""Unreal Engine command-line helper for agents.

Finds the engine for a project and wraps UnrealBuildTool, UAT BuildCookRun and
UnrealEditor-Cmd with safe defaults. Standard library only.

    python ue.py env      --project ./MyGame
    python ue.py running  --project ./MyGame
    python ue.py build    --project ./MyGame [--target editor|game] [--config Development]
    python ue.py package  --project ./MyGame --platform Win64 --config Shipping [--out DIR]
    python ue.py test     --project ./MyGame --filter MyGame
    python ue.py python   --project ./MyGame --script scripts/editor/fix.py

Every command accepts --engine (or UE_ENGINE_ROOT) to skip discovery and
--dry-run to print the command instead of running it. build, package and
python refuse to run while an editor or game of the project is running,
because Unreal refuses to build beside a live game module.
"""

from __future__ import annotations

import argparse
import configparser
import json
import os
import platform
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path

HOST = platform.system()  # "Windows", "Darwin", "Linux"
HOST_PLATFORM = {"Windows": "Win64", "Darwin": "Mac", "Linux": "Linux"}.get(HOST, "Win64")
GUID_RE = re.compile(r"^\{?[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}\}?$")


class UEError(Exception):
    pass


# --------------------------------------------------------------------------- project

def find_uproject(path: str | None) -> Path:
    p = Path(path or ".").resolve()
    if p.is_file() and p.suffix == ".uproject":
        return p
    if p.is_dir():
        found = sorted(p.glob("*.uproject"))
        if len(found) == 1:
            return found[0]
        if len(found) > 1:
            raise UEError(f"several .uproject files in {p}; pass one with --project")
    raise UEError(f"no .uproject found at {p}")


def read_uproject(uproject: Path) -> dict:
    try:
        return json.loads(uproject.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise UEError(f"{uproject} is not valid JSON: {exc}") from exc


def target_names(uproject: Path) -> dict:
    """Map 'editor'/'game' to target names from Source/*.Target.cs."""
    src = uproject.parent / "Source"
    names = {}
    for f in sorted(src.glob("*.Target.cs")) if src.is_dir() else []:
        stem = f.name[: -len(".Target.cs")]
        if stem.endswith("Editor"):
            names.setdefault("editor", stem)
        elif not stem.endswith(("Server", "Client")):
            names.setdefault("game", stem)
    return names


# --------------------------------------------------------------------------- engine

def _is_engine_root(p: Path) -> bool:
    return (p / "Engine" / "Build" / "BatchFiles").is_dir()


def _launcher_dat_paths() -> list[Path]:
    if HOST == "Windows":
        base = os.environ.get("PROGRAMDATA", r"C:\ProgramData")
        return [Path(base) / "Epic" / "UnrealEngineLauncher" / "LauncherInstalled.dat"]
    if HOST == "Darwin":
        return [Path.home() / "Library/Application Support/Epic/UnrealEngineLauncher/LauncherInstalled.dat"]
    return [Path.home() / ".config/Epic/UnrealEngineLauncher/LauncherInstalled.dat"]


def _from_launcher_dat(version: str) -> list[Path]:
    hits = []
    for dat in _launcher_dat_paths():
        if not dat.is_file():
            continue
        try:
            data = json.loads(dat.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            continue
        for item in data.get("InstallationList", []):
            if item.get("AppName") == f"UE_{version}" and item.get("InstallLocation"):
                hits.append(Path(item["InstallLocation"]))
    return hits


def _install_ini_paths() -> list[Path]:
    if HOST == "Darwin":
        return [Path.home() / "Library/Application Support/Epic/UnrealEngine/Install.ini"]
    if HOST == "Linux":
        return [Path.home() / ".config/Epic/UnrealEngine/Install.ini"]
    return []


def _from_install_ini(key: str) -> list[Path]:
    hits = []
    for ini in _install_ini_paths():
        if not ini.is_file():
            continue
        cp = configparser.ConfigParser(strict=False)
        cp.optionxform = str  # keep case
        try:
            cp.read(ini, encoding="utf-8")
        except configparser.Error:
            continue
        if cp.has_section("Installations"):
            for k, v in cp.items("Installations"):
                if k.strip("{}").lower() == key.strip("{}").lower():
                    hits.append(Path(v))
    return hits


def _from_registry(key: str, is_guid: bool) -> list[Path]:
    if HOST != "Windows":
        return []
    try:
        import winreg  # type: ignore
    except ImportError:
        return []
    hits = []
    try:
        if is_guid:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Epic Games\Unreal Engine\Builds") as k:
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(k, i)
                    except OSError:
                        break
                    if name.strip("{}").lower() == key.strip("{}").lower():
                        hits.append(Path(value))
                    i += 1
        else:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, rf"SOFTWARE\EpicGames\Unreal Engine\{key}") as k:
                value, _ = winreg.QueryValueEx(k, "InstalledDirectory")
                hits.append(Path(value))
    except OSError:
        pass
    return hits


def _default_dirs(version: str) -> list[Path]:
    if HOST == "Windows":
        return [Path(r"C:\Program Files\Epic Games") / f"UE_{version}"]
    if HOST == "Darwin":
        return [Path("/Users/Shared/Epic Games") / f"UE_{version}"]
    return [Path.home() / f"UnrealEngine-{version}", Path.home() / "UnrealEngine"]


def find_engine(uproject: Path, override: str | None) -> tuple[Path, str]:
    """Return (engine root, how it was found)."""
    explicit = override or os.environ.get("UE_ENGINE_ROOT")
    if explicit:
        root = Path(explicit).resolve()
        if root.name == "Engine" and _is_engine_root(root.parent):
            root = root.parent
        if not _is_engine_root(root):
            raise UEError(f"{root} is not an engine root (no Engine/Build/BatchFiles)")
        return root, "--engine/UE_ENGINE_ROOT"

    assoc = str(read_uproject(uproject).get("EngineAssociation", "")).strip()
    if not assoc:
        for parent in uproject.parents:
            if _is_engine_root(parent):
                return parent, "parent directory (empty EngineAssociation)"
        raise UEError("EngineAssociation is empty and no engine found above the project; pass --engine")

    is_guid = bool(GUID_RE.match(assoc))
    candidates: list[tuple[Path, str]] = []
    if is_guid:
        candidates += [(p, "source build registry") for p in _from_registry(assoc, True)]
        candidates += [(p, "Install.ini") for p in _from_install_ini(assoc)]
    else:
        candidates += [(p, "LauncherInstalled.dat") for p in _from_launcher_dat(assoc)]
        candidates += [(p, "registry") for p in _from_registry(assoc, False)]
        candidates += [(p, "Install.ini") for p in _from_install_ini(assoc)]
        candidates += [(p, "default install path") for p in _default_dirs(assoc)]
    for path, how in candidates:
        if _is_engine_root(path):
            return path.resolve(), how
    raise UEError(f"engine '{assoc}' not found (checked {len(candidates)} locations); "
                  f"set UE_ENGINE_ROOT or pass --engine")


def engine_version(root: Path) -> str:
    bv = root / "Engine" / "Build" / "Build.version"
    try:
        d = json.loads(bv.read_text(encoding="utf-8-sig"))
        return f"{d.get('MajorVersion')}.{d.get('MinorVersion')}.{d.get('PatchVersion')}"
    except (OSError, json.JSONDecodeError):
        return "unknown"


def tool_paths(root: Path) -> dict:
    bf = root / "Engine" / "Build" / "BatchFiles"
    if HOST == "Windows":
        build, uat = bf / "Build.bat", bf / "RunUAT.bat"
        editors = [root / "Engine/Binaries/Win64/UnrealEditor-Cmd.exe", root / "Engine/Binaries/Win64/UnrealEditor.exe"]
    elif HOST == "Darwin":
        build, uat = bf / "Mac" / "Build.sh", bf / "RunUAT.sh"
        editors = [root / "Engine/Binaries/Mac/UnrealEditor-Cmd",
                   root / "Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor"]
    else:
        build, uat = bf / "Linux" / "Build.sh", bf / "RunUAT.sh"
        editors = [root / "Engine/Binaries/Linux/UnrealEditor-Cmd", root / "Engine/Binaries/Linux/UnrealEditor"]
    editor_cmd = next((e for e in editors if e.exists()), editors[0])
    return {"build": build, "uat": uat, "editor_cmd": editor_cmd}


# --------------------------------------------------------------------------- processes

def running_processes(uproject: Path) -> list[dict]:
    """Unreal editor, Live Coding and game processes that block builds."""
    project = uproject.stem.lower()
    pats = ("unrealeditor", "livecodingconsole", project)
    rows: list[tuple[str, str, str]] = []
    try:
        if HOST == "Windows":
            ps = ("Get-CimInstance Win32_Process | ForEach-Object { "
                  "\"$($_.ProcessId)`t$($_.Name)`t$($_.CommandLine)\" }")
            out = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True,
                                 text=True, timeout=60).stdout
            for line in out.splitlines():
                parts = line.split("\t", 2)
                if len(parts) >= 2:
                    rows.append((parts[0], parts[1], parts[2] if len(parts) > 2 else ""))
        else:
            out = subprocess.run(["ps", "-axo", "pid=,comm=,args="], capture_output=True, text=True,
                                 timeout=30).stdout
            for line in out.splitlines():
                parts = line.split(None, 2)
                if len(parts) >= 2:
                    rows.append((parts[0], Path(parts[1]).name, parts[2] if len(parts) > 2 else ""))
    except (OSError, subprocess.SubprocessError):
        return []
    me = str(os.getpid())
    hits = []
    for pid, name, cmd in rows:
        low = name.lower()
        if pid == me or "python" in low or not any(low.startswith(p) for p in pats):
            continue
        hits.append({"pid": pid, "name": name,
                     "this_project": project in cmd.lower() or low.startswith(project),
                     "command": cmd[:200]})
    return hits


def guard_not_running(uproject: Path, force: bool, what: str) -> None:
    procs = running_processes(uproject)
    blocking = [p for p in procs if p["this_project"] or p["name"].lower().startswith("livecodingconsole")]
    unknown = [p for p in procs if p not in blocking and not p["command"]]
    if (blocking or unknown) and not force:
        lines = "\n".join(f"  pid {p['pid']}: {p['name']}" for p in blocking + unknown)
        raise UEError(f"refusing to {what}: an editor, Live Coding console or game of this project is "
                      f"running (Unreal refuses to build beside a live game module):\n{lines}\n"
                      f"Save in the editor, close it, then retry. --force skips this check.")


# --------------------------------------------------------------------------- running

def win_cmdline(cmd: list[str]) -> str:
    """Quote for Unreal's own parser: -Key="value with spaces", not "-Key=value with spaces".

    UnrealEditor reads the raw Windows command line, and FParse::Value only honours a quote
    that follows the '='. UBT and UAT (.NET) accept this form too.
    """
    out = []
    for arg in cmd:
        if arg and not re.search(r'[\s"]', arg):
            out.append(arg)
        elif arg.startswith("-") and "=" in arg:
            key, val = arg.split("=", 1)
            out.append(f'{key}="{val}"')
        else:
            out.append(f'"{arg}"')
    return " ".join(out)


def show(cmd: list[str]) -> str:
    if HOST == "Windows":
        return win_cmdline(cmd)
    return " ".join(shlex.quote(c) for c in cmd)


def run(cmd: list[str], log: Path | None, dry: bool) -> int:
    print(f"$ {show(cmd)}", flush=True)
    if dry:
        return 0
    if not Path(cmd[0]).exists():
        raise UEError(f"tool not found: {cmd[0]}")
    fh = None
    if log:
        log.parent.mkdir(parents=True, exist_ok=True)
        fh = open(log, "w", encoding="utf-8", errors="replace")
        print(f"(log: {log})", flush=True)
    start = time.time()
    try:
        proc = subprocess.Popen(win_cmdline(cmd) if HOST == "Windows" else cmd,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, encoding="utf-8", errors="replace")
        assert proc.stdout is not None
        for line in proc.stdout:
            sys.stdout.write(line)
            if fh:
                fh.write(line)
        code = proc.wait()
    finally:
        if fh:
            fh.close()
    print(f"exit {code} after {time.time() - start:.0f} s", flush=True)
    return code


def log_path(uproject: Path, name: str) -> Path:
    return uproject.parent / "Saved" / "Logs" / f"agent_{name}_{time.strftime('%Y%m%d_%H%M%S')}.log"


# --------------------------------------------------------------------------- commands

def cmd_env(a) -> int:
    up = find_uproject(a.project)
    info = {"uproject": str(up), "engine_association": read_uproject(up).get("EngineAssociation", ""),
            "targets": target_names(up), "host_platform": HOST_PLATFORM}
    try:
        root, how = find_engine(up, a.engine)
        info.update({"engine_root": str(root), "found_by": how, "engine_version": engine_version(root),
                     **{k: str(v) for k, v in tool_paths(root).items()}})
    except UEError as exc:
        info["engine_error"] = str(exc)
    info["running"] = running_processes(up)
    print(json.dumps(info, indent=2))
    return 0 if "engine_root" in info else 1


def cmd_running(a) -> int:
    up = find_uproject(a.project)
    procs = running_processes(up)
    print(json.dumps(procs, indent=2))
    return 1 if any(p["this_project"] for p in procs) else 0


def cmd_build(a) -> int:
    up = find_uproject(a.project)
    names = target_names(up)
    if not names:
        print("No Source/*.Target.cs: a Blueprint-only project has nothing to compile.")
        return 0
    target = a.target_name or names.get(a.target)
    if not target:
        raise UEError(f"no {a.target} target in Source/ (found: {names})")
    if not a.dry_run:
        guard_not_running(up, a.force, "build")
    root, _ = find_engine(up, a.engine)
    tools = tool_paths(root)
    plat = a.platform or HOST_PLATFORM
    cmd = [str(tools["build"]), target, plat, a.config, f"-Project={up}", "-WaitMutex"]
    if a.max_parallel:
        cmd.append(f"-MaxParallelActions={a.max_parallel}")
    if a.force:
        cmd.append("-NoHotReloadFromIDE")
    return run(cmd, log_path(up, f"build_{target}"), a.dry_run)


def cmd_package(a) -> int:
    up = find_uproject(a.project)
    if not a.dry_run:
        guard_not_running(up, a.force, "package")
    root, _ = find_engine(up, a.engine)
    tools = tool_paths(root)
    out = Path(a.out).resolve() if a.out else up.parent / "Packaged" / a.platform
    cmd = [str(tools["uat"]), "BuildCookRun", f"-project={up}", "-noP4", "-utf8output", "-unattended",
           f"-platform={a.platform}", f"-clientconfig={a.config}", "-build", "-cook", "-stage", "-pak",
           "-archive", f"-archivedirectory={out}"]
    if a.platform == "Win64":
        cmd.append("-prereqs")
    if a.config == "Shipping":
        cmd.append("-nodebuginfo")
    if a.maps:
        cmd.append("-map=" + "+".join(a.maps))
    if a.skip_editor_build:
        cmd.append("-nocompileeditor")
    cmd += a.extra or []
    if a.platform.lower() == "wasm" and not a.extra:
        print("note: for the web target, copy the exact BuildCookRun flags the editor logs when packaging "
              "from the Platforms menu, and pass them with --extra.", flush=True)
    code = run(cmd, log_path(up, f"package_{a.platform}_{a.config}"), a.dry_run)
    if code == 0 and not a.dry_run:
        size = sum(f.stat().st_size for f in out.rglob("*") if f.is_file()) if out.exists() else 0
        print(f"archive: {out} ({size / 1e6:.0f} MB unzipped; weigh the zip, not the folder)")
    return code


def cmd_test(a) -> int:
    up = find_uproject(a.project)
    root, _ = find_engine(up, a.engine)
    tools = tool_paths(root)
    report = Path(a.report).resolve() if a.report else up.parent / "Saved" / "Automation" / "agent"
    cmd = [str(tools["editor_cmd"]), str(up), f"-ExecCmds=Automation RunTests {a.filter}",
           "-TestExit=Automation Test Queue Empty", f"-ReportExportPath={report}",
           "-unattended", "-nopause", "-nosplash", "-nosound", "-log"]
    if not a.render:
        cmd.append("-nullrhi")
    if not a.dry_run:
        if any(p["this_project"] for p in running_processes(up)):
            print("warning: an editor of this project is running; headless tests may contend for files.")
        (report / "index.json").unlink(missing_ok=True)  # never read a previous run's report
    code = run(cmd, log_path(up, "test"), a.dry_run)
    if a.dry_run:
        return code
    index = report / "index.json"
    if not index.is_file():
        print(f"no test report at {index}; read the log above")
        return code or 1
    data = json.loads(index.read_text(encoding="utf-8-sig"))
    failed = [t for t in data.get("tests", []) if str(t.get("state", "")).lower() == "fail"]
    print(f"tests: {data.get('succeeded', '?')} passed, {data.get('succeededWithWarnings', 0)} with warnings, "
          f"{data.get('failed', len(failed))} failed, {data.get('notRun', 0)} not run")
    for t in failed:
        print(f"  FAIL {t.get('fullTestPath') or t.get('testDisplayName')}")
        for e in t.get("entries", [])[:3]:
            msg = (e.get("event") or {}).get("message", "")
            if msg:
                print(f"       {msg[:200]}")
    if data.get("succeeded", 0) == 0 and not failed:
        print(f"no tests matched '{a.filter}'")
        return 1
    return 1 if failed or code else 0


def cmd_python(a) -> int:
    up = find_uproject(a.project)
    script = Path(a.script).resolve()
    if not script.is_file():
        raise UEError(f"script not found: {script}")
    if not a.dry_run:
        guard_not_running(up, a.force, "run a headless editor on this project")
    root, _ = find_engine(up, a.engine)
    tools = tool_paths(root)
    arg = str(script) if not a.script_args else " ".join([str(script)] + a.script_args)
    cmd = [str(tools["editor_cmd"]), str(up), "-run=pythonscript", f"-script={arg}",
           "-unattended", "-nopause", "-nosplash"]
    return run(cmd, log_path(up, f"python_{script.stem}"), a.dry_run)


# --------------------------------------------------------------------------- main

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("--project", help="project folder or .uproject (default: current folder)")
        p.add_argument("--engine", help="engine root (default: UE_ENGINE_ROOT or discovery)")
        p.add_argument("--dry-run", action="store_true", help="print the command, do not run it")
        return p

    common(sub.add_parser("env", help="print engine, tools and running processes as JSON"))
    common(sub.add_parser("running", help="list editor/game processes; exit 1 if this project's run"))

    b = common(sub.add_parser("build", help="compile a target with UnrealBuildTool"))
    b.add_argument("--target", choices=["editor", "game"], default="editor")
    b.add_argument("--target-name", help="explicit target name (overrides --target)")
    b.add_argument("--config", default="Development")
    b.add_argument("--platform", help=f"default: {HOST_PLATFORM}")
    b.add_argument("--max-parallel", type=int, help="cap parallel compile actions")
    b.add_argument("--force", action="store_true",
                   help="skip the running-editor check and pass -NoHotReloadFromIDE")

    p = common(sub.add_parser("package", help="BuildCookRun: build, cook, stage, pak, archive"))
    p.add_argument("--platform", default=HOST_PLATFORM, help="Win64, Mac, Linux, Wasm, ...")
    p.add_argument("--config", default="Shipping", choices=["Development", "Shipping", "Test", "DebugGame"])
    p.add_argument("--out", help="archive directory (default: <project>/Packaged/<platform>)")
    p.add_argument("--maps", nargs="+", help="maps to cook (default: project packaging settings)")
    p.add_argument("--skip-editor-build", action="store_true", help="pass -nocompileeditor")
    p.add_argument("--extra", nargs=argparse.REMAINDER, help="extra BuildCookRun arguments, verbatim")
    p.add_argument("--force", action="store_true", help="skip the running-editor check")

    t = common(sub.add_parser("test", help="run automation tests headless"))
    t.add_argument("--filter", required=True, help="test name prefix, e.g. MyGame or MyGame.Scoring")
    t.add_argument("--report", help="report folder (default: <project>/Saved/Automation/agent)")
    t.add_argument("--render", action="store_true", help="run with a renderer (no -nullrhi)")

    y = common(sub.add_parser("python", help="run an editor Python script headless"))
    y.add_argument("--script", required=True)
    y.add_argument("--script-args", nargs=argparse.REMAINDER, help="arguments passed to the script")
    y.add_argument("--force", action="store_true", help="skip the running-editor check")

    a = ap.parse_args(argv)
    handlers = {"env": cmd_env, "running": cmd_running, "build": cmd_build, "package": cmd_package,
                "test": cmd_test, "python": cmd_python}
    try:
        return handlers[a.cmd](a)
    except UEError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
