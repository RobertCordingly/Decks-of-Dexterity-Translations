import os
import json

def apply_changes():
    # Existing code...

    passed_dir = "../passed_changes"
    language_dir = ".."  # or adjust if language files are elsewhere

    for filename in os.listdir(passed_dir):
        if filename.endswith(".json"):
            path = os.path.join(passed_dir, filename)
            with open(path, "r", encoding="utf-8") as f:
                patch = json.load(f)

            lang = patch.get("language")
            edits = patch.get("edits", {})

            lang_file_path = os.path.join(language_dir, f"{lang}.json")
            if not os.path.exists(lang_file_path):
                print(f"Language file not found for '{lang}': {lang_file_path}")
                continue

            with open(lang_file_path, "r", encoding="utf-8") as f:
                lang_data = json.load(f)

            updated = 0
            for key, new_val in edits.items():
                if key in lang_data and lang_data[key] != new_val:
                    lang_data[key] = new_val
                    updated += 1

            if updated > 0:
                with open(lang_file_path, "w", encoding="utf-8") as f:
                    json.dump(lang_data, f, ensure_ascii=False, indent=2)
                print(f"Updated {updated} keys in {lang_file_path}")
            else:
                print(f"No updates needed for {lang_file_path}")

            # Handle FIND/REPLACE edits
            for key, val in edits.items():
                if key.startswith("FIND: ") and val.startswith("REPLACE: "):
                    find_text = key[len("FIND: "):]
                    replace_text = val[len("REPLACE: "):]
                    replaced = 0
                    for k in lang_data:
                        if isinstance(lang_data[k], str) and find_text in lang_data[k]:
                            lang_data[k] = lang_data[k].replace(find_text, replace_text)
                            replaced += 1
                    if replaced > 0:
                        print(f"Replaced '{find_text}' with '{replace_text}' in {replaced} entries of {lang_file_path}")

apply_changes()