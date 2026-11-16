#!/usr/bin/env python3
"""Scan an Unreal editor, cook, UAT or build log for known blockers.

    python check_log.py --project ./MyGame          # newest log in Saved/Logs
    python check_log.py --log path/to/Cook.log
    python check_log.py --project ./MyGame --module LogMyGame

Prints each known problem once, with its count, first line number, what it
means and what to do. Exit code 1 if a blocker or error was found, else 0.
Standard library only.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# (name, severity, regex, meaning, action)
PATTERNS = [
    ("stale-module", "blocker", r"Can't find class descriptor",
     "The editor runs an older build of the game module than the content expects.",
     "Save nothing from this editor. Close it, run a full editor build, reopen, check again."),
    ("live-coding-lock", "blocker", r"Unable to build while Live Coding is active",
     "A running editor or game of the project holds the module.",
     "Close the editor, its Live Coding console and any running game, then build."),
    ("gamefeature-scan-rule", "blocker", r"do(?:es)? not include an entry for assets of type GameFeatureData",
     "Agent toolset plugins enabled GameFeatures; the cook needs a scan rule.",
     "Add a PrimaryAssetTypesToScan entry for GameFeatureData, or keep the toolsets editor-only."),
    ("duplicate-asset-id", "blocker", r"Duplicate Asset ID",
     "Two primary assets share an ID (often a copied folder with a label in it).",
     "Delete or rename the duplicate; it breaks the cook."),
    ("mcp-port", "error", r"(Failed to (?:listen|bind)|Unable to bind).{0,80}(?:8000|port)",
     "The MCP server could not open its port.",
     "Another process owns the port. Pick another port and regenerate the client config."),
    ("crash", "blocker", r"(Fatal error|Assertion failed|Unhandled Exception|=== Critical error: ===)",
     "The process crashed.",
     "Read the call stack below the first occurrence; check Saved/Crashes."),
    ("ensure", "error", r"Ensure condition failed",
     "An ensure fired: a bug the engine survived.",
     "Read the condition and call stack; fix before it becomes a crash."),
    ("msvc-error", "error", r"\berror C\d{4}:",
     "C++ compile error (MSVC).", "Fix the first error; later ones often follow from it."),
    ("clang-error", "error", r"\.(?:cpp|h|inl):\d+:\d+: (?:fatal )?error:",
     "C++ compile error (clang).", "Fix the first error; later ones often follow from it."),
    ("linker-error", "error", r"(\berror LNK\d{4}|undefined reference to|ld: symbol\(s\) not found)",
     "Link error: a symbol is declared but not built, or a module dependency is missing.",
     "Check Build.cs dependencies and *_API export macros."),
    ("uht-error", "error", r"(LogCompile: Error|\.h\(\d+\): Error:)",
     "Reflection (UHT) error in a header.", "Fix the UCLASS/USTRUCT/UPROPERTY declaration named."),
    ("cook-error", "error", r"LogCook: Error",
     "The cook failed on an asset.", "Read the asset path; often a missing or stale reference."),
    ("failed-load", "error", r"(Failed to load '|LogLinker: (?:Warning|Error): .*Failed to load|Can't find file for asset)",
     "A reference points at an asset that does not exist on disk.",
     "Fix up redirectors, re-save the referencer, or restore the asset."),
    ("missing-object", "warning", r"Failed to find object",
     "A path or name lookup at runtime failed.", "Check soft references and paths loaded by string."),
    ("python-error", "error", r"LogPython: Error",
     "An editor Python script raised.", "Read the traceback; fix and re-run the script."),
    ("blueprint-error", "error", r"(LogBlueprint: Error|Blueprint.{0,60}failed to compile)",
     "A Blueprint does not compile.", "Open it or query it over MCP; fix, compile, save."),
    ("shader-error", "error", r"(Failed to compile Material|Shader compilation failed|LogShaderCompilers: (?:Warning|Error):.{0,40}fail)",
     "A material or shader failed. The game keeps running and draws a fallback, silently.",
     "Fix the material; look at the affected view after the fix."),
    ("uat-exit", "error", r"AutomationTool exiting with ExitCode=(?!0\b)\d+",
     "UAT failed.", "Find the first ERROR line above it."),
    ("uat-error", "error", r"(^\s*|: )ERROR: ",
     "UAT or UBT reported an error.", "Read the line; the first one is usually the cause."),
    ("texture-pot", "warning", r"(power of two|NonPowerOfTwo|non-power-of-two)",
     "A texture is not power-of-two: no mips, no streaming.", "Resize the source or set power-of-two import."),
    ("unsaved", "warning", r"(unsaved|dirty) package",
     "Packages were left unsaved.", "Save and verify before closing or handing over the editor."),
]

SEVERITY_ORDER = {"blocker": 0, "error": 1, "warning": 2}


def newest_log(project: Path) -> Path:
    logs = project / "Saved" / "Logs"
    candidates = [p for p in logs.glob("*.log") if "-backup-" not in p.name] if logs.is_dir() else []
    if not candidates:
        raise SystemExit(f"error: no logs in {logs}")
    return max(candidates, key=lambda p: p.stat().st_mtime)


def scan(path: Path, module: str | None):
    compiled = [(n, s, re.compile(r, re.IGNORECASE if n in ("texture-pot", "unsaved") else 0), m, a)
                for n, s, r, m, a in PATTERNS]
    hits: dict[str, dict] = {}
    module_warnings = []
    module_re = re.compile(rf"\b{re.escape(module)}: (Warning|Error)") if module else None
    with open(path, encoding="utf-8-sig", errors="replace") as fh:
        for i, line in enumerate(fh, 1):
            for name, sev, rx, meaning, action in compiled:
                if rx.search(line):
                    h = hits.setdefault(name, {"severity": sev, "count": 0, "line": i,
                                               "text": line.strip()[:240], "meaning": meaning,
                                               "action": action})
                    h["count"] += 1
            if module_re and module_re.search(line):
                module_warnings.append((i, line.strip()[:240]))
    return hits, module_warnings


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--project", help="project folder; scans the newest Saved/Logs/*.log")
    src.add_argument("--log", help="a specific log file")
    ap.add_argument("--module", help="log category of the project (e.g. LogMyGame) to count its warnings")
    a = ap.parse_args(argv)

    path = Path(a.log) if a.log else newest_log(Path(a.project or ".").resolve())
    if not path.is_file():
        print(f"error: {path} not found", file=sys.stderr)
        return 2
    hits, module_lines = scan(path, a.module)
    print(f"log: {path}")
    if not hits and not module_lines:
        print("no known problems found")
        return 0
    for name, h in sorted(hits.items(), key=lambda kv: (SEVERITY_ORDER[kv[1]["severity"]], kv[1]["line"])):
        print(f"\n[{h['severity'].upper()}] {name}: {h['count']}x, first at line {h['line']}")
        print(f"  {h['text']}")
        print(f"  meaning: {h['meaning']}")
        print(f"  action:  {h['action']}")
    if module_lines:
        print(f"\n[{a.module}] {len(module_lines)} warning/error line(s); first ones:")
        for i, t in module_lines[:10]:
            print(f"  {i}: {t}")
    bad = any(h["severity"] in ("blocker", "error") for h in hits.values())
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
