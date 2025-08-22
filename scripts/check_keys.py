#!/usr/bin/env python3

import json
import sys
from pathlib import Path

def load_json(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {path}: {e}")
        sys.exit(1)

def compare_keys(file1, file2):
    keys1 = set(file1.keys())
    keys2 = set(file2.keys())

    missing_keys = keys1 - keys2
    if missing_keys:
        print("The following keys are missing in the second file:")
        for key in sorted(missing_keys):
            print(f"  {key}")
        return False
    else:
        print("All keys from the first file are present in the second file.")
        return True

def main():
    if len(sys.argv) != 3:
        print("Usage: check_keys.py <path_to_first_json> <path_to_second_json>")
        sys.exit(1)

    path1 = Path(sys.argv[1])
    path2 = Path(sys.argv[2])

    json1 = load_json(path1)
    json2 = load_json(path2)

    if not isinstance(json1, dict) or not isinstance(json2, dict):
        print("Both JSON files must contain a top-level object (dictionary).")
        sys.exit(1)

    compare_keys(json1, json2)

if __name__ == "__main__":
    main()