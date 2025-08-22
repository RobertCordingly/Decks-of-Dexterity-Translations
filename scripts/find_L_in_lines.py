#!/usr/bin/env python3
from pathlib import Path
import re
import ast
import json
import shutil
from typing import Iterable, List

# ---- CONFIGURABLE PATHS ----
ROOT = Path("/Users/robertcordingly/Documents/Decks of Dexterity/DecksOfDexterity")
TRANSLATIONS_JSON = Path("/Users/robertcordingly/Documents/Decks of Dexterity/Translations/Decks-of-Dexterity-Translations/vt.json")
BACKUP_JSON = TRANSLATIONS_JSON.with_suffix(TRANSLATIONS_JSON.suffix + ".bak")
PLACEHOLDER_VALUE = "MISSING TRANSLATION"
# ----------------------------

# Matches L("...") or L('...') and captures the first argument string (handles escaped quotes)
L_FIRST_ARG = re.compile(
    r"""L\s*\(\s*(?:
            "((?:[^"\\]|\\.)*)"      # group 1: double-quoted
          | '((?:[^'\\]|\\.)*)'      # group 2: single-quoted
        )""",
    re.VERBOSE | re.ASCII
)

def dedup_preserve_order(items: Iterable[str]) -> List[str]:
    seen = set()
    out = []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out

def strip_comments(text: str) -> str:
    """Remove // and /* */ comments from GML source (naïve but effective)."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)  # block comments
    text = re.sub(r"//.*", "", text)                        # line comments
    return text

def extract_strings_from_gml(root: Path) -> List[str]:
    found: List[str] = []
    for gml_path in root.rglob("*.gml"):
        try:
            code = gml_path.read_text(encoding="utf-8", errors="ignore")
            code = strip_comments(code)
            for m in L_FIRST_ARG.finditer(code):
                raw = m.group(1) if m.group(1) is not None else m.group(2)
                s = ast.literal_eval(f'"{raw}"')  # unescape
                s = s.replace("\n", "\\n")        # normalize JSON-style newlines
                found.append(s)
        except Exception as e:
            print(f"# Skipped {gml_path} due to error: {e}")
    return dedup_preserve_order(found)

def load_translations_dict(json_path: Path) -> dict:
    if not json_path.exists():
        return {}
    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("Translations JSON must be an object of key/value pairs.")
        return data  # maintains insertion order in 3.7+

# --- Minimal JSON-aware appender (preserves existing formatting) ---

def find_top_level_closing_brace_index(text: str) -> int:
    """Return index of the final '}' that closes the top-level object (not inside strings)."""
    in_str = False
    escape = False
    depth = 0
    last_closing = -1
    for i, ch in enumerate(text):
        if in_str:
            if escape:
                escape = False
            elif ch == '\\':
                escape = True
            elif ch == '"':
                in_str = False
            continue
        else:
            if ch == '"':
                in_str = True
            elif ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    last_closing = i
    return last_closing

def detect_indent_before_closing(text: str, closing_idx: int) -> str:
    """Infer indentation used for keys by looking at whitespace before the closing brace line."""
    # Find the start of the line containing the closing brace
    line_start = text.rfind("\n", 0, closing_idx) + 1
    # Count spaces/tabs between line_start and closing brace
    indent_chars = []
    for ch in text[line_start:closing_idx]:
        if ch in (" ", "\t"):
            indent_chars.append(ch)
        else:
            indent_chars = []  # non-space before brace; treat as no indent on this line
            break
    # If file uses typical 2 spaces for keys, we'll mirror the line's indentation;
    # keys themselves will use that indent.
    return "".join(indent_chars) if indent_chars else "  "

def append_entries_preserving_format(json_path: Path, new_keys: List[str], placeholder: str):
    """
    Append "key": "placeholder" entries just before the final '}' of the top-level object,
    preserving existing file formatting and order.
    """
    # Read original text
    original = json_path.read_text(encoding="utf-8")

    # Sanity: ensure it parses as a dict (and we know if it's empty)
    obj = json.loads(original)
    if not isinstance(obj, dict):
        raise ValueError("Translations JSON must be a top-level object.")
    is_empty = (len(obj) == 0)

    # Locate top-level closing brace
    close_idx = find_top_level_closing_brace_index(original)
    if close_idx == -1:
        raise ValueError("Could not locate top-level closing brace in JSON.")

    # Determine indentation style for keys
    key_indent = detect_indent_before_closing(original, close_idx)
    # Determine newline style (LF/CRLF) from file
    newline = "\r\n" if "\r\n" in original and original.count("\r\n") >= original.count("\n") else "\n"

    # Build insertion block
    # Each entry: <key_indent><json.dumps(key)>: <json.dumps(value)>
    entries = [f'{key_indent}{json.dumps(k, ensure_ascii=False)}: {json.dumps(placeholder, ensure_ascii=False)}'
               for k in new_keys]

    insertion = ""
    if is_empty:
        # Insert:
        # \n<entry1>,\n<entry2>...\n
        insertion = newline + (f",{newline}".join(entries)) + newline
    else:
        # Add a comma after the last existing entry, then our entries.
        # We assume the existing file is valid JSON without trailing comma.
        insertion = "," + newline + (f",{newline}".join(entries)) + newline

    # Splice: before close brace + insertion + close brace + rest (usually nothing after })
    new_text = original[:close_idx] + insertion + original[close_idx:]

    # Ensure ending newline like original (optional)
    if not new_text.endswith(("\n", "\r", "\r\n")) and original.endswith(("\n", "\r", "\r\n")):
        new_text += newline

    # Write back
    json_path.write_text(new_text, encoding="utf-8")

def save_with_backup_append(json_path: Path, new_keys: List[str], placeholder: str):
    # Make backup
    if json_path.exists():
        try:
            shutil.copy2(json_path, BACKUP_JSON)
            print(f"# Backup created: {BACKUP_JSON}")
        except Exception as e:
            print(f"# WARN: failed to create backup: {e}")

    if not json_path.exists():
        # Create a minimal object with new keys, preserving order
        key_indent = "  "
        newline = "\n"
        entries = [f'{key_indent}{json.dumps(k, ensure_ascii=False)}: {json.dumps(placeholder, ensure_ascii=False)}'
                   for k in new_keys]
        content = "{" + (newline + (f",{newline}".join(entries)) + newline if entries else "") + "}"
        json_path.write_text(content + newline, encoding="utf-8")
        print(f"# Created new translations file: {json_path}")
    else:
        append_entries_preserving_format(json_path, new_keys, placeholder)
        print(f"# Appended {len(new_keys)} new key(s) to: {json_path}")

def main():
    # 1) Gather all first-arg strings from L(...) across .gml files
    gml_strings = extract_strings_from_gml(ROOT)

    # 2) Load translations to know existing keys
    translations = load_translations_dict(TRANSLATIONS_JSON)
    existing_keys = set(translations.keys())

    # 3) Determine missing keys (preserve discovery order)
    missing = [s for s in gml_strings if s not in existing_keys]

    # 4) Save back, appending only new keys at end (no reformatting)
    if missing:
        save_with_backup_append(TRANSLATIONS_JSON, missing, PLACEHOLDER_VALUE)
    else:
        print("# No new strings to add — translations already complete for discovered keys.")

    # Summary
    print(f"# Discovered strings: {len(gml_strings)}")
    print(f"# Existing keys:      {len(existing_keys)}")
    print(f"# Added missing:      {len(missing)}")

if __name__ == "__main__":
    main()