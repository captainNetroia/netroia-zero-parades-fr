"""
translate_po_claude.py
Adapts translate_po.py to use the Anthropic Claude API directly.

Usage:
    python translate_po_claude.py --input fr_translation.po --output fr_translated.po

Set ANTHROPIC_API_KEY in environment before running.
"""

import json
import logging
import os
import re
import shutil
import sys
import threading
import time
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import polib
from tqdm import tqdm
import anthropic

from language_codes import ASSET_PATHS, DISPLAY_NAMES

logger = logging.getLogger(__name__)

CONTEXT_FILE = Path(__file__).parent / "llm_translation_context.md"

DEFAULT_MODEL = "claude-haiku-4-5-20251001"
MAX_BATCH_CHARS = 4000

SYSTEM_PROMPT_TEMPLATE = """\
You are an expert literary video game translator working on *Zero Parades*, a dark narrative RPG
with rich emotional depth, complex characters, and a unique atmospheric tone.
You will translate strings from {source_lang} to {target_lang}.

{context}

---

CORE PHILOSOPHY — ADAPT, DON'T JUST TRANSLATE:
You are not a dictionary. You are a storyteller translating into French.
- Capture the EMOTION first, the words second. A dying character's last words must
  feel like a last breath, not a grammar exercise.
- Use natural, idiomatic French. Never translate word-for-word if it sounds unnatural.
- Dark moments must feel dark. Humorous moments must land as jokes. Tender moments
  must resonate emotionally.
- Short, punchy lines stay short and punchy. Long, melancholic sentences keep their rhythm.
- Characters have distinct voices — a cynical spy speaks differently from a naive recruit.
  If the source text has personality, preserve it in French.

TRANSLATION RULES:
1. Return ONLY a valid JSON array of strings — one translated string per input string,
   in the same order. No keys, no explanations, no markdown fences.
2. Preserve ALL inline markup exactly: <i>…</i>, <shy>, *emphasis*, {{variables}}.
3. Never translate proper nouns, character names, place names, or the terms listed
   in the "Things to never translate" section above.
4. Match the tone: literary, dark, occasionally humorous. Short lines stay short.
5. If a string is untranslatable (e.g. a single symbol or markup-only), return it unchanged.
6. The response must be parseable by json.loads(). Escape special characters properly.
7. Prefer literary French over administrative French — "mourir" over "décéder",
   "tuer" over "éliminer", "peur" over "appréhension" unless the context demands formality.
8. For UI/menu strings (very short, 1-3 words): translate functionally and clearly.
9. For dialogue: prioritize emotional truth. A character in pain sounds in pain.
"""


def load_context() -> str:
    if CONTEXT_FILE.exists():
        return CONTEXT_FILE.read_text(encoding="utf-8")
    return ""


def make_claude_client():
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        sys.exit("Error: ANTHROPIC_API_KEY environment variable not set.")
    return anthropic.Anthropic(api_key=key)


def call_claude(client, model: str, system: str, user: str, max_retries: int = 4) -> str:
    delay = 2
    for attempt in range(max_retries):
        try:
            resp = client.messages.create(
                model=model,
                max_tokens=8192,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            return resp.content[0].text
        except anthropic.RateLimitError:
            time.sleep(delay)
            delay *= 2
        except anthropic.APIError:
            if attempt == max_retries - 1:
                raise
            time.sleep(delay)
            delay *= 2
    raise RuntimeError("Max retries exceeded")


def parse_json_array(text: str) -> list[str]:
    text = re.sub(r"<think(?:ing)?>.*?</think(?:ing)?>", "", text, flags=re.DOTALL)
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON array found. Raw: {text[:200]!r}")
    return json.loads(text[start:end + 1])


def translate_batch(texts: list[str], system: str, client, model: str, _depth: int = 0) -> list[str]:
    if not texts:
        return []
    user = (
        f"Translate the following {len(texts)} strings. "
        "Return ONLY a JSON array of the translated strings in the same order.\n\n"
        + json.dumps(texts, ensure_ascii=False)
    )
    try:
        result = parse_json_array(call_claude(client, model, system, user))
        result = [s if isinstance(s, str) else "" for s in result]
        if len(result) != len(texts):
            raise ValueError(f"Claude returned {len(result)} strings for {len(texts)} inputs.")
        return result
    except (ValueError, json.JSONDecodeError):
        if _depth >= 3 or len(texts) == 1:
            logger.warning("Batch of %d still failing — will retry on next run.", len(texts))
            return [""] * len(texts)
        mid = len(texts) // 2
        return (
            translate_batch(texts[:mid], system, client, model, _depth + 1)
            + translate_batch(texts[mid:], system, client, model, _depth + 1)
        )


def translate_po(input_path, output_path, target_lang, source_lang, model,
                 batch_size, save_every, preview=3, parallel=1):
    po = polib.pofile(str(input_path), encoding="utf-8")
    total = len(po)
    todo = [e for e in po if not e.msgstr]
    done = total - len(todo)

    if done:
        logger.info("Reprise : %d/%d déjà traduits, %d restants.", done, total, len(todo))
    else:
        logger.info("Démarrage : %d entrées à traduire.", total)

    if not todo:
        logger.info("Rien à faire.")
        return

    context = load_context()
    system = SYSTEM_PROMPT_TEMPLATE.format(
        source_lang=source_lang, target_lang=target_lang, context=context
    )
    client = make_claude_client()

    batches: list[list] = []
    current: list = []
    current_chars = 0
    for entry in todo:
        chars = len(entry.msgid)
        if current and (len(current) >= batch_size or current_chars + chars > MAX_BATCH_CHARS):
            batches.append(current)
            current = []
            current_chars = 0
        current.append(entry)
        current_chars += chars
    if current:
        batches.append(current)

    failed_batches: list[int] = []
    recent_times: list[float] = []
    save_lock = threading.Lock()
    batches_done = 0

    def process_batch(batch_idx, batch):
        texts = [e.msgid for e in batch]
        t0 = time.time()
        try:
            translations = translate_batch(texts, system, client, model)
            return batch_idx, translations, None, time.time() - t0
        except Exception as exc:
            return batch_idx, None, exc, time.time() - t0

    with tqdm(total=total, initial=done, unit="entry", desc=f"Traduction -> {target_lang}") as pbar:
        executor = ThreadPoolExecutor(max_workers=parallel)
        futures = {}
        try:
            futures = {
                executor.submit(process_batch, i, batch): (i, batch)
                for i, batch in enumerate(batches)
            }
            for future in as_completed(futures):
                batch_idx, batch = futures[future]
                _, translations, exc, elapsed = future.result()

                if exc is not None:
                    tqdm.write(f"  [batch {batch_idx}] ERREUR: {exc} — ignoré.")
                    failed_batches.append(batch_idx)
                else:
                    for entry, translation in zip(batch, translations):
                        entry.msgstr = translation

                    with save_lock:
                        recent_times.append(elapsed)
                        if len(recent_times) > 10:
                            recent_times.pop(0)
                        avg_t = sum(recent_times) / len(recent_times)
                        rem = max(0, len(batches) - batches_done - 1)
                    eta_s = rem * avg_t / max(1, parallel)
                    if eta_s >= 3600:
                        eta = f"{int(eta_s // 3600)}h{int(eta_s % 3600 // 60):02d}m"
                    elif eta_s >= 60:
                        eta = f"{int(eta_s // 60)}m{int(eta_s % 60):02d}s"
                    else:
                        eta = f"{eta_s:.0f}s"

                    if preview > 0:
                        col = max(25, (shutil.get_terminal_size().columns - 5) // 2)
                        tqdm.write(f"  {'Source':<{col}} | Traduction")
                        tqdm.write(f"  {'-' * col}-+-{'-' * col}")
                        for entry in batch[-preview:]:
                            s = entry.msgid.replace("\n", " ")
                            d = entry.msgstr.replace("\n", " ")
                            src = (s[:col - 3] + "...") if len(s) > col else s
                            dst = (d[:col - 3] + "...") if len(d) > col else d
                            tqdm.write(f"  {src:<{col}} | {dst}")
                        tqdm.write(f"  {elapsed:.1f}s · avg {avg_t:.1f}s · ~{rem} batches · ETA {eta}\n")

                pbar.update(len(batch))
                with save_lock:
                    batches_done += 1
                    if batches_done % save_every == 0:
                        po.save(str(output_path))

        except KeyboardInterrupt:
            tqdm.write("\nInterrompu — sauvegarde en cours...")
            for f in futures:
                f.cancel()
        finally:
            executor.shutdown(wait=True)
            po.save(str(output_path))

    po.save(str(output_path))
    translated = len([e for e in po if e.msgstr])
    logger.info("Terminé. %d/%d entrées traduites -> %s", translated, total, output_path)
    if failed_batches:
        logger.warning("%d batches échoués — relancer la commande pour réessayer.", len(failed_batches))


def main():
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description="Traduit un .po Zero Parades avec Claude")
    parser.add_argument("--input",       required=True,  help="Fichier .po source")
    parser.add_argument("--output",      required=True,  help="Fichier .po de sortie")
    parser.add_argument("--target-lang", default="French", help="Langue cible (default: French)")
    parser.add_argument("--source-lang", default="de",
                        choices=list(ASSET_PATHS), help="Langue source (default: de)")
    parser.add_argument("--model",       default=DEFAULT_MODEL, help=f"Modèle Claude (default: {DEFAULT_MODEL})")
    parser.add_argument("--batch-size",  type=int, default=25)
    parser.add_argument("--save-every",  type=int, default=5)
    parser.add_argument("--preview",     type=int, default=3)
    parser.add_argument("--parallel",    type=int, default=3)
    args = parser.parse_args()

    source_lang_name = DISPLAY_NAMES.get(args.source_lang, args.source_lang)
    input_path  = Path(args.input)
    output_path = Path(args.output)

    if output_path.exists():
        logger.info("Fichier de sortie existant — reprise depuis %s", output_path)
        work_input = output_path
    else:
        work_input = input_path

    logger.info("Modele: %s  Batch: %d  Parallel: %d", args.model, args.batch_size, args.parallel)
    logger.info("Source: %s  Cible: %s", source_lang_name, args.target_lang)

    translate_po(
        input_path=work_input,
        output_path=output_path,
        target_lang=args.target_lang,
        source_lang=source_lang_name,
        model=args.model,
        batch_size=args.batch_size,
        save_every=args.save_every,
        preview=args.preview,
        parallel=args.parallel,
    )


if __name__ == "__main__":
    main()
