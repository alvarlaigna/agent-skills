#!/usr/bin/env python3
"""Advisory checks for common AI-sounding Estonian risks.

This script is intentionally dependency-free and conservative. It is not a
grammar oracle; pair it with EKI, Sõnaveeb/ÕS, EKI teatmik, or estonian-mcp for
authoritative checks.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8")


AI_FILLER_PATTERNS = [
    (r"\bon oluline m[äa�\?]rkida, et\b", "Likely filler: consider deleting or stating the point directly."),
    (r"\btasub mainida, et\b", "Likely filler: consider deleting or making the claim concrete."),
    (r"\bantud kontekstis\b", "Often bureaucratic/AI-like: consider 'selles kontekstis' or omit."),
    (r"\bl[äa�\?]bi selle\b", "Possible English/Russian calque: consider 'sellega', 'seeläbi', or a verb."),
    (r"\bparim(ad|aid|ate)? praktik(ad|aid|ate)?\b", "Possible English calque: consider 'head tavad' or a specific practice."),
    (r"\bteeb m[õo�\?]tet\b", "English calque: Estonian usually uses 'on mõtet' or rephrases."),
    (r"\bpakub v[õo�\?]imalust\b", "Often vague: name the concrete action or benefit."),
    (r"\binnovaatiline lahendus\b", "Generic marketing phrase: make the benefit specific."),
]

MONTHS_WEEKDAYS_LANGS = [
    "Esmaspäev",
    "Teisipäev",
    "Kolmapäev",
    "Neljapäev",
    "Reede",
    "Laupäev",
    "Pühapäev",
    "Jaanuar",
    "Veebruar",
    "Märts",
    "Aprill",
    "Mai",
    "Juuni",
    "Juuli",
    "August",
    "September",
    "Oktoober",
    "November",
    "Detsember",
    "Eesti keel",
    "Inglise keel",
    "Vene keel",
    "Soome keel",
    "Saksa keel",
    "Prantsuse keel",
]

COMMON_VAGUE_WORDS = [
    "oluline",
    "tõhus",
    "lihtne",
    "mugav",
    "kaasaegne",
    "lahendus",
    "kogemus",
    "võimalus",
    "võimaldab",
    "pakub",
]


@dataclass
class Finding:
    category: str
    message: str
    excerpt: str


def read_text(path: str | None) -> str:
    if path:
        return Path(path).read_text(encoding="utf-8")
    data = sys.stdin.buffer.read()
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode(sys.stdin.encoding or "utf-8", errors="replace")


def sentence_split(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]


def excerpt(text: str, start: int, end: int, width: int = 45) -> str:
    left = max(0, start - width)
    right = min(len(text), end + width)
    return re.sub(r"\s+", " ", text[left:right]).strip()


def check_patterns(text: str) -> list[Finding]:
    findings: list[Finding] = []
    for pattern, message in AI_FILLER_PATTERNS:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            findings.append(Finding("ai-style", message, excerpt(text, match.start(), match.end())))
    return findings


def check_capitalization(text: str) -> list[Finding]:
    findings: list[Finding] = []
    for word in MONTHS_WEEKDAYS_LANGS:
        for match in re.finditer(rf"(?<![.!?\n]\s){re.escape(word)}", text):
            findings.append(
                Finding(
                    "capitalization",
                    f"Check capitalization: '{word}' is often lowercase in running Estonian text.",
                    excerpt(text, match.start(), match.end()),
                )
            )
    return findings


def check_numbers(text: str) -> list[Finding]:
    findings: list[Finding] = []
    for match in re.finditer(r"\b\d+\.\d+\b", text):
        findings.append(
            Finding(
                "numbers",
                "Possible decimal separator issue: Estonian usually uses a comma, e.g. 3,14.",
                excerpt(text, match.start(), match.end()),
            )
        )
    for match in re.finditer(r"\b\d{1,3}(?:,\d{3})+\b", text):
        findings.append(
            Finding(
                "numbers",
                "Possible thousands separator issue: Estonian usually uses a space, e.g. 1 000 000.",
                excerpt(text, match.start(), match.end()),
            )
        )
    return findings


def check_abbreviations(text: str) -> list[Finding]:
    findings: list[Finding] = []
    pattern = r"\b(?:API|MCP|URL|PDF|OÜ|AS|MTÜ)(?:ga|le|lt|st|sse|s|ks|ni|na|ta)\b"
    for match in re.finditer(pattern, text):
        findings.append(
            Finding(
                "abbreviation",
                "Possible missing hyphen before case ending on abbreviation, e.g. API-ga or MCP-st.",
                excerpt(text, match.start(), match.end()),
            )
        )
    return findings


def check_long_sentences(text: str, max_words: int) -> list[Finding]:
    findings: list[Finding] = []
    for sentence in sentence_split(text):
        words = re.findall(r"\b[\wõäöüšžÕÄÖÜŠŽ-]+\b", sentence)
        if len(words) > max_words:
            findings.append(
                Finding(
                    "sentence-length",
                    f"Long sentence ({len(words)} words): consider splitting or tightening.",
                    sentence[:160] + ("..." if len(sentence) > 160 else ""),
                )
            )
    return findings


def check_repetition(text: str, threshold: int) -> list[Finding]:
    words = [
        w.lower()
        for w in re.findall(r"\b[\wõäöüšžÕÄÖÜŠŽ-]{4,}\b", text)
        if not w.isdigit()
    ]
    counts = Counter(words)
    findings: list[Finding] = []

    for word in COMMON_VAGUE_WORDS:
        if counts[word] >= threshold:
            findings.append(
                Finding(
                    "repetition",
                    f"Vague word repeated {counts[word]} times: '{word}'. Consider concrete alternatives.",
                    word,
                )
            )

    for word, count in counts.most_common(10):
        if count >= max(threshold + 1, 4) and word not in COMMON_VAGUE_WORDS:
            findings.append(
                Finding(
                    "repetition",
                    f"Surface word repeated {count} times: '{word}'. Check whether repetition is intentional.",
                    word,
                )
            )
    return findings


def collect_findings(text: str, max_words: int, repetition_threshold: int) -> list[Finding]:
    findings: list[Finding] = []
    findings.extend(check_patterns(text))
    findings.extend(check_capitalization(text))
    findings.extend(check_numbers(text))
    findings.extend(check_abbreviations(text))
    findings.extend(check_long_sentences(text, max_words))
    findings.extend(check_repetition(text, repetition_threshold))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", help="UTF-8 text file. Reads stdin when omitted.")
    parser.add_argument("--max-sentence-words", type=int, default=28)
    parser.add_argument("--repetition-threshold", type=int, default=3)
    args = parser.parse_args()

    text = read_text(args.path)
    if not text.strip():
        print("No text provided.", file=sys.stderr)
        return 2

    findings = collect_findings(text, args.max_sentence_words, args.repetition_threshold)

    print("Estonian advisory check")
    print("Note: advisory only; verify grammar with EKI, Sõnaveeb/ÕS, EKI teatmik, or estonian-mcp.")
    print()

    if not findings:
        print("No deterministic warnings found.")
        return 0

    for idx, item in enumerate(findings, start=1):
        print(f"{idx}. [{item.category}] {item.message}")
        print(f"   Excerpt: {item.excerpt}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
