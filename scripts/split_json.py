#!/usr/bin/env python3
"""
Split a flat JSON object into N‑key chunks (default 400 keys per file).

Example
-------
$ python split_json_chunks.py strings.json --outdir ./chunks --size 400
"""

import argparse
import json
import math
import os
from pathlib import Path

CHUNK_SIZE_DEFAULT = 400


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Split a JSON dict into fixed‑size chunks.")
    parser.add_argument("infile", type=Path, help="Path to the source JSON file.")
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path("./chunks"),
        help="Directory to write the chunk files (created if missing).",
    )
    parser.add_argument(
        "--size",
        type=int,
        default=CHUNK_SIZE_DEFAULT,
        help=f"Number of keys per chunk (default {CHUNK_SIZE_DEFAULT}).",
    )
    parser.add_argument(
        "--prefix",
        type=str,
        default="chunk",
        help='Filename prefix for chunks (e.g., "chunk_001.json").',
    )
    return parser.parse_args()


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("Top‑level JSON element must be an object/dictionary.")
    return data


def write_chunk(data: dict, out_path: Path) -> None:
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main() -> None:
    args = parse_args()

    # Ensure output directory exists
    args.outdir.mkdir(parents=True, exist_ok=True)

    source_dict = load_json(args.infile)
    keys = list(source_dict.keys())
    total_chunks = math.ceil(len(keys) / args.size)

    for idx in range(total_chunks):
        start = idx * args.size
        end = start + args.size
        chunk_keys = keys[start:end]
        chunk_dict = {k: source_dict[k] for k in chunk_keys}

        outfile = args.outdir / f"{args.prefix}_{idx + 1:03d}.json"
        write_chunk(chunk_dict, outfile)

        print(f"Wrote {len(chunk_dict):>3} keys → {outfile}")

    print(f"Done. {total_chunks} chunk file(s) written to {args.outdir}")


if __name__ == "__main__":
    main()