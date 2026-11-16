#!/usr/bin/env python3
"""Audit source art and audio before importing it into Unreal.

    python audit_source_assets.py SourceArt/
    python audit_source_assets.py docs/assets --max-texture 2048 --strict

Textures (PNG, JPEG, TGA, BMP): size, power-of-two, oversize.
Audio (WAV): format, channels, rate, length, peak and RMS level, clipping,
silence, loop-seam jump for files that look like loops, stereo music, size.

Errors (exit 1): unreadable files, clipping, float or compressed WAV.
Warnings (exit 1 only with --strict): everything else.
Standard library only.
"""

from __future__ import annotations

import argparse
import array
import math
import re
import struct
import sys
import wave
from pathlib import Path

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".tga", ".bmp"}


def is_pot(n: int) -> bool:
    return n > 0 and (n & (n - 1)) == 0


def image_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    ext = path.suffix.lower()
    if ext == ".png":
        if data[:8] != b"\x89PNG\r\n\x1a\n":
            raise ValueError("not a PNG")
        return struct.unpack(">II", data[16:24])
    if ext in (".jpg", ".jpeg"):
        i = 2
        while i + 9 < len(data):
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                h, w = struct.unpack(">HH", data[i + 5:i + 9])
                return w, h
            if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
                i += 2
                continue
            i += 2 + struct.unpack(">H", data[i + 2:i + 4])[0]
        raise ValueError("no JPEG frame header")
    if ext == ".tga":
        return struct.unpack("<HH", data[12:16])
    if ext == ".bmp":
        w, h = struct.unpack("<ii", data[18:26])
        return w, abs(h)
    raise ValueError("unsupported image")


def wav_stats(path: Path) -> dict:
    with open(path, "rb") as fh:
        head = fh.read(40)
    if head[:4] != b"RIFF" or head[8:12] != b"WAVE":
        raise ValueError("not a RIFF/WAVE file")
    # Find the fmt chunk to report non-PCM formats clearly.
    data = path.read_bytes()
    pos, fmt_tag = 12, None
    while pos + 8 <= len(data):
        cid, size = data[pos:pos + 4], struct.unpack("<I", data[pos + 4:pos + 8])[0]
        if cid == b"fmt ":
            fmt_tag = struct.unpack("<H", data[pos + 8:pos + 10])[0]
            break
        pos += 8 + size + (size & 1)
    if fmt_tag == 3:
        raise ValueError("32-bit float WAV; export 16-bit PCM")
    if fmt_tag not in (1, 0xFFFE):
        raise ValueError(f"compressed WAV (format tag {fmt_tag}); export 16-bit PCM")

    with wave.open(str(path), "rb") as w:
        ch, width, rate, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        raw = w.readframes(n)
    if width == 2:
        samples = array.array("h")
        samples.frombytes(raw)
        if sys.byteorder == "big":
            samples.byteswap()
        full = 32767
    elif width == 3:
        samples = array.array("i", (int.from_bytes(raw[i:i + 3], "little", signed=True)
                                    for i in range(0, len(raw) - 2, 3)))
        full = 8388607
    elif width == 4:
        samples = array.array("i")
        samples.frombytes(raw)
        if sys.byteorder == "big":
            samples.byteswap()
        full = 2147483647
    elif width == 1:
        samples = array.array("i", (b - 128 for b in raw))
        full = 127
    else:
        raise ValueError(f"unsupported sample width {width}")

    if not samples:
        return {"channels": ch, "rate": rate, "bits": width * 8, "seconds": 0.0,
                "peak_db": -math.inf, "rms_db": -math.inf, "clipped": 0, "seam": 0.0}
    peak = max(abs(s) for s in samples)
    clipped = sum(1 for s in samples if abs(s) >= full)
    step = max(1, len(samples) // 200000)  # sample the RMS on long files
    sub = samples[::step]
    rms = math.sqrt(sum(s * s for s in sub) / len(sub))

    def db(v: float) -> float:
        return 20 * math.log10(v / full) if v > 0 else -math.inf

    first = [samples[c] for c in range(ch)]
    last = [samples[len(samples) - ch + c] for c in range(ch)]
    seam = max(abs(a - b) for a, b in zip(first, last)) / full
    return {"channels": ch, "rate": rate, "bits": width * 8, "seconds": n / rate if rate else 0.0,
            "peak_db": db(peak), "rms_db": db(rms), "clipped": clipped, "seam": seam}


def audit(root: Path, a) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    loop_re = re.compile(a.loop_pattern)
    music_re = re.compile(a.music_pattern)
    files = sorted(p for p in root.rglob("*") if p.is_file()) if root.is_dir() else [root]
    for p in files:
        rel = p.relative_to(root) if root.is_dir() else p.name
        ext = p.suffix.lower()
        size_mb = p.stat().st_size / 1e6
        if ext in IMAGE_EXT:
            try:
                w, h = image_size(p)
            except (ValueError, struct.error, OSError) as exc:
                errors.append(f"{rel}: unreadable image ({exc})")
                continue
            if not (is_pot(w) and is_pot(h)):
                warnings.append(f"{rel}: {w}x{h} is not power-of-two (no mips or streaming; fine for UI only)")
            if max(w, h) > a.max_texture:
                warnings.append(f"{rel}: {w}x{h} is larger than {a.max_texture}")
        elif ext == ".wav":
            try:
                s = wav_stats(p)
            except (ValueError, wave.Error, EOFError, struct.error, OSError) as exc:
                errors.append(f"{rel}: {exc}")
                continue
            tag = f"{rel}: {s['channels']}ch {s['rate']} Hz {s['bits']}-bit {s['seconds']:.1f} s"
            if s["clipped"]:
                errors.append(f"{tag}: {s['clipped']} clipped samples")
            if s["peak_db"] < -60:
                warnings.append(f"{tag}: silent or near-silent (peak {s['peak_db']:.1f} dBFS)")
            elif s["rms_db"] < -35:
                warnings.append(f"{tag}: quiet (RMS {s['rms_db']:.1f} dBFS); normalize or raise gain")
            if loop_re.search(p.name) and s["seam"] > a.seam_threshold:
                warnings.append(f"{tag}: loop seam jumps {s['seam']:.2f} of full scale; it will click")
            if music_re.search(p.name) and s["channels"] > 1:
                warnings.append(f"{tag}: stereo music; mono halves the size")
            if s["rate"] not in (44100, 48000):
                warnings.append(f"{tag}: unusual sample rate")
        else:
            continue
        if size_mb > a.max_mb:
            warnings.append(f"{rel}: {size_mb:.0f} MB is larger than {a.max_mb} MB")
    return errors, warnings


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", help="folder or single file to audit")
    ap.add_argument("--max-texture", type=int, default=4096)
    ap.add_argument("--max-mb", type=float, default=50.0)
    ap.add_argument("--loop-pattern", default=r"(?i)loop", help="regex on file names treated as loops")
    ap.add_argument("--music-pattern", default=r"(?i)(music|^mus_|_mus_)", help="regex on music file names")
    ap.add_argument("--seam-threshold", type=float, default=0.05)
    ap.add_argument("--strict", action="store_true", help="fail on warnings too")
    a = ap.parse_args(argv)

    root = Path(a.path).resolve()
    if not root.exists():
        print(f"error: {root} not found", file=sys.stderr)
        return 2
    errors, warnings = audit(root, a)
    for e in errors:
        print(f"ERROR   {e}")
    for w in warnings:
        print(f"WARNING {w}")
    print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors or (a.strict and warnings) else 0


if __name__ == "__main__":
    sys.exit(main())
