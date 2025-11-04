# utils_translit.py
import re
import io
import os
from typing import Tuple, List, Dict
from PIL import Image
from pdf2image import convert_from_bytes
import pytesseract
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate
from langdetect import detect as lang_detect
import zipfile
from tqdm import tqdm

# --- Unicode ranges for script detection (best-effort) ---
SCRIPT_RANGES = [
    ("Devanagari", (0x0900, 0x097F)),
    ("Bengali", (0x0980, 0x09FF)),
    ("Gurmukhi", (0x0A00, 0x0A7F)),
    ("Gujarati", (0x0A80, 0x0AFF)),
    ("Oriya", (0x0B00, 0x0B7F)),
    ("Tamil", (0x0B80, 0x0BFF)),
    ("Telugu", (0x0C00, 0x0C7F)),
    ("Kannada", (0x0C80, 0x0CFF)),
    ("Malayalam", (0x0D00, 0x0D7F)),
    ("Latin", (0x0041, 0x007A)),
    ("Arabic", (0x0600, 0x06FF)),
    ("Hebrew", (0x0590, 0x05FF)),
    ("Cyrillic", (0x0400, 0x04FF)),
]

# Map user-friendly target names to sanscript attributes (if present)
SANSCRIPT_MAP = {k: getattr(sanscript, k) for k in dir(sanscript) if k.isupper()}


def detect_script(text: str) -> str:
    counts = {}
    for ch in text:
        cp = ord(ch)
        for name, (lo, hi) in SCRIPT_RANGES:
            if lo <= cp <= hi:
                counts[name] = counts.get(name, 0) + 1
    if not counts:
        return "Unknown"
    return max(counts, key=counts.get)


# Heuristic to pick input scheme if input is Latin/Romanized
def guess_input_scheme(text: str) -> str:
    # If text contains diacritics common to IAST (ā ī ū ṛ ṭ ḍ ṃ ṇ ś ṣ etc.) -> IAST
    iast_chars = re.compile(r"[āīūṛṝṅñṭḍṇśṣḥṃĀĪŪṚṜḶḸ]")
    if iast_chars.search(text):
        return "IAST"
    # If text uses uppercase markers like . or ^ commonly in ITRANS -> ITRANS
    # Hard fallback to ITRANS for simple ASCII transliteration
    # If text looks already in Devanagari/Bengali etc, return that
    scr = detect_script(text)
    if scr == "Devanagari":
        return "DEVANAGARI"
    if scr == "Bengali":
        return "BENGALI"
    # check for SLP1 patterns (all-lowercase with numbers?) - skip complex heuristics
    # default
    return "ITRANS"


# OCR helpers
def ocr_image_bytes(img_bytes: bytes, tesseract_lang: str = "eng") -> str:
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    return pytesseract.image_to_string(img, lang=tesseract_lang)


def ocr_pdf_bytes(pdf_bytes: bytes, tesseract_lang: str = "eng") -> str:
    texts = []
    images = convert_from_bytes(pdf_bytes)
    for page in images:
        txt = pytesseract.image_to_string(page, lang=tesseract_lang)
        texts.append(txt)
    return "\n".join(texts)


# Transliterate using indic-transliteration with error handling
def transliterate_text(text: str, src_scheme: str, tgt_scheme: str) -> str:
    # Normalize scheme names
    if src_scheme not in SANSCRIPT_MAP:
        raise ValueError(f"Unknown source scheme: {src_scheme}")
    if tgt_scheme not in SANSCRIPT_MAP:
        raise ValueError(f"Unknown target scheme: {tgt_scheme}")
    try:
        return transliterate(text, SANSCRIPT_MAP[src_scheme], SANSCRIPT_MAP[tgt_scheme])
    except Exception as e:
        # fallback: return error message as text
        return f"[TRANSLIT ERROR] {e}"


# Batch processing & zip creation
def batch_transliterate_filetexts(file_texts: Dict[str, str], src_scheme: str, tgt_schemes: List[str]) -> bytes:
    """
    file_texts: dict filename->text
    returns bytes of zip archive containing converted files named <orig>__<tgt>.txt
    """
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for fname, text in tqdm(file_texts.items()):
            for tgt in tgt_schemes:
                out = transliterate_text(text, src_scheme, tgt)
                outname = f"{os.path.splitext(fname)[0]}__{tgt}.txt"
                zf.writestr(outname, out.encode("utf-8"))
    mem.seek(0)
    return mem.read()
