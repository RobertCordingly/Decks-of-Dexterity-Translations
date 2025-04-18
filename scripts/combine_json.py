

#!/usr/bin/env python3
"""
combine_json.py

Combine JSON chunk files named `chunk_###.json` inside a folder into a
single JSON file while **preserving the original key order**—
all keys from `chunk_001.json` appear first, then from `chunk_002.json`,
and so on.

Usage
-----
    python combine_json.py <folder_path> [output_file]

If *output_file* is omitted, the script writes `combined.json` inside
*folder_path*.

Notes
-----
* Each chunk may be wrapped in Markdown fences (```json … ```).
  These fences are stripped automatically before parsing.
* Duplicate keys are ignored after their first appearance (a warning is
  printed to stderr).
"""

import json
import os
import re
import sys
from collections import OrderedDict


FENCE_RE = re.compile(r"^```(?:json)?\s*$", re.IGNORECASE)


def strip_fence(text: str) -> str:
    """Remove leading  ```json and trailing ``` fences if present."""
    lines = text.strip().splitlines()
    if lines and FENCE_RE.match(lines[0]):
        lines = lines[1:]  # drop opening fence
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]  # drop closing fence
    return "\n".join(lines)


def load_chunk(path: str) -> "OrderedDict[str, str]":
    """Load a single chunk file and return an OrderedDict of its items."""
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()
    cleaned = strip_fence(raw)
    return json.loads(cleaned, object_pairs_hook=OrderedDict)


def main(folder: str, output: str = "combined.json") -> None:
    combined: "OrderedDict[str, str]" = OrderedDict()

    chunk_files = sorted(
        f
        for f in os.listdir(folder)
        if f.startswith("chunk_") and f.endswith(".json")
    )

    if not chunk_files:
        print(f"No chunk_*.json files found in {folder}", file=sys.stderr)
        sys.exit(1)

    for fname in chunk_files:
        path = os.path.join(folder, fname)
        try:
            data = load_chunk(path)
        except json.JSONDecodeError as exc:
            print(f"⚠️  Skipping {fname}: JSON error → {exc}", file=sys.stderr)
            continue

        for key, value in data.items():
            if key in combined:
                print(
                    f"⚠️  Duplicate key '{key}' in {fname} ignored "
                    "(already present from an earlier chunk)",
                    file=sys.stderr,
                )
                continue
            combined[key] = value

    out_path = os.path.join(folder, output)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)

    print(f"✅ Combined {len(chunk_files)} files into {out_path}")
    print(f"   Total keys: {len(combined)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python combine_json.py <folder_path> [output_file]")
        sys.exit(1)

    folder_arg = sys.argv[1]
    output_arg = sys.argv[2] if len(sys.argv) > 2 else "combined.json"
    main(folder_arg, output_arg)