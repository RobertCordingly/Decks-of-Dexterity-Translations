#!/usr/bin/env python3.10
"""
translate_chunks.py - batch-translate JSON chunks with a local Gemma LLM.

Requires: requests (pip install requests) and tqdm (pip install tqdm) - tqdm is
used only for a neat “file x / N” progress bar; remove if you'd rather not add
the dependency.
"""

import os
import json
import requests
from tqdm import tqdm

# ─── Configuration ──────────────────────────────────────────────────────────
GEMMA_URL = "http://localhost:1234/v1/chat/completions"
MODEL_NAME = "gemma-3-27b-it"
TEMPERATURE = 0.7              
CHUNKS_DIR = os.path.join(os.path.dirname(__file__), "..", "chunks")
OUT_DIR   = os.path.join(os.path.dirname(__file__), "..", "translated_chunks")
os.makedirs(OUT_DIR, exist_ok=True)

SYSTEM_PROMPT = """Your job is to translate text of a video game from English to another language. Output nothing else other than the translated text. For context, the text is from a card game with a variety of keywords that need to be consistent throughout the translation. Translate the keywords to the other language and maintain them throughout. Important keywords include:

Health Points (HP): A resource used to determine if the player is alive. 
Burns: A resource that can be spent by "burning" cards, discarding and drawing a new card. Some cards have special effects when burnt.
Fusion Points (FP): A resource increased by fusing cards making them more powerful
Critical Hit Chance (CHC): The chance a hit deals critical damage.
Critical Damage Multiplier (CDM): The multiplier to damage of a critical hit.
COMBO: A counter for the number of turns chained together.
Energy: A unit of electricity that deals damage over time.
Fragile: A card with fragile is destroyed when played.
Flare: A card that is temporarily removed when burnt.
One-Shot: A card that is temporarily removed when played.
Enflame: A card that is destroyed when played.

Finally, capitalization should be maintained in each language and string length should be as close as possible between the languages. The text is supplied via a json file where the key is the string in English and the value is the translated version.

Sometimes strings will have numbers or verbs inserted into them. These points are marked with %n% where n is the index of the insertion. For example a card may have a description for “Fire 5 bullets.” and in the translation file it will be “Fire %1% bullets.” Place those insertion points in the correct place.

Please translate the attached json data from English to German. The keys should be in English and the values should be in German. This file contains English as the keys and Spanish as the values for reference."""
# ────────────────────────────────────────────────────────────────────────────

def send_translation_request(json_payload: str) -> str:
    """
    Calls the local Gemma model with streaming=true and returns the raw,
    concatenated content from the assistant (i.e. the full translated JSON).
    """
    req_body = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": json_payload}
        ],
        "temperature": TEMPERATURE,
        "max_tokens": -1,
        "stream": True
    }

    response = requests.post(GEMMA_URL, json=req_body, stream=True)
    response.raise_for_status()

    translated_buffer = []        # hold incoming token fragments
    print("\n  ↳ streaming tokens...", flush=True)
    for line in response.iter_lines():
        if not line:
            continue

        # OpenAI‑style server‑sent events use "data: ..." and finish with "[DONE]"
        line = line.decode("utf-8")
        if line.strip() == "data: [DONE]":
            break
        if not line.startswith("data:"):
            continue

        event = json.loads(line[len("data: "):])
        delta = event["choices"][0]["delta"]
        if "content" in delta:
            token = delta["content"]
            translated_buffer.append(token)
            
            #print(token, end="", flush=True)   # live feedback

    print()   # newline after stream
    return "".join(translated_buffer).strip()

def main() -> None:
    files = [f for f in os.listdir(CHUNKS_DIR) if f.lower().endswith(".json")]
    if not files:
        print("No .json files found in", CHUNKS_DIR)
        return

    for fname in tqdm(files, desc="Translating files", unit="file"):
        src_path = os.path.join(CHUNKS_DIR, fname)
        with open(src_path, "r", encoding="utf‑8") as f:
            chunk_text = f.read()

        try:
            translated_text = send_translation_request(chunk_text)
        except Exception as exc:
            print(f"\n❌ Error translating {fname}: {exc}")
            continue

        # Expect the model to return a well‑formed JSON string
        try:
            translated_obj = json.loads(translated_text)
        except json.JSONDecodeError:
            print(f"\n⚠️  Model output for {fname} wasn't valid JSON. "
                  "Saving raw text so you can inspect it.")
            translated_obj = translated_text  # still save something

        out_path = os.path.join(OUT_DIR, fname)
        with open(out_path, "w", encoding="utf-8") as out_f:
            # If we got a dict, pretty‑print it; otherwise just dump the raw text
            if isinstance(translated_obj, dict):
                json.dump(translated_obj, out_f,
                          ensure_ascii=False, indent=2)
            else:
                out_f.write(translated_obj)

        tqdm.write(f"✅ {fname} → {os.path.relpath(out_path)}")

if __name__ == "__main__":
    main()