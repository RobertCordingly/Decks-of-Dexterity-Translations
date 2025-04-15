import requests
import os
import json

# Utilize local LibreTranslate installation for translations back to English. Launch with libretranslate
def translate(text, source_lang="en", target_lang="en"):
    url = "http://127.0.0.1:5000/translate"
    payload = {
        "q": text,
        "source": source_lang,
        "target": target_lang,
        "format": "text"
    }

    response = requests.post(url, json=payload)
    response.raise_for_status()

    return response.json()['translatedText']

# Example usage
input_dir = "../recent_changes"

for filename in os.listdir(input_dir):
    if filename.endswith(".json"):

        print("------------------------------------------------------------")
        print("------------------------------------------------------------")
        print("------------------------------------------------------------")

        path = os.path.join(input_dir, filename)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        lang = data.get("language", "es")

        if lang == "brpt":
            lang = "pt"

        edits = data.get("edits", {})

        print(f"\nReviewing file: {filename}")
        print("=" * 60)

        for original, translated in edits.items():
            try:
                english = translate(translated, source_lang=lang, target_lang="en")
            except Exception as e:
                english = f"[Translation failed: {e}]"

            print(f"KEY:     {original}")
            #print(f"CURRENT:     {translated}")
            print(f"BACK:    {english}")
            print("-" * 60)

        while True:
            confirm = input("Accept changes? (Y/N): ").strip().lower()
            if confirm == 'y':
                passed_dir = "../passed_changes"
                os.makedirs(passed_dir, exist_ok=True)
                os.rename(path, os.path.join(passed_dir, filename))
                print(f"Moved {filename} to passed_changes.")
                break
            elif confirm == 'n':
                denied_dir = "../denied_changes"
                os.makedirs(denied_dir, exist_ok=True)
                os.rename(path, os.path.join(denied_dir, filename))
                print(f"Moved {filename} to denied_changes.")
                break
            else:
                print("Please enter 'Y' or 'N'.")