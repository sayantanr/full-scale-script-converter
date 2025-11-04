# api_fastapi.py
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import PlainTextResponse, StreamingResponse, JSONResponse
from utils_translit import ocr_image_bytes, ocr_pdf_bytes, guess_input_scheme, transliterate_text
import io, zipfile
from typing import List

app = FastAPI(title="Transliteration API (indic-transliteration)")

@app.post("/transliterate")
async def transliterate_endpoint(
    tgt: List[str] = Form(...),
    src: str = Form("Auto"),
    tess_lang: str = Form("eng"),
    file: UploadFile = File(...)
):
    data = await file.read()
    name = file.filename
    # extract text
    if name.lower().endswith(".txt"):
        try:
            text = data.decode("utf-8")
        except:
            text = data.decode("latin-1")
    elif name.lower().endswith(".pdf"):
        text = ocr_pdf_bytes(data, tesseract_lang=tess_lang)
    else:
        text = ocr_image_bytes(data, tesseract_lang=tess_lang)
    if not text:
        return JSONResponse({"error": "No text extracted"}, status_code=400)
    src_scheme = src if src != "Auto" else guess_input_scheme(text)
    results = {}
    for t in tgt:
        results[t] = transliterate_text(text, src_scheme, t)
    # if one target, return plain text
    if len(tgt) == 1:
        return PlainTextResponse(results[tgt[0]])
    # else return zip
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as zf:
        for scheme, content in results.items():
            zf.writestr(f"{name}__{scheme}.txt", content.encode("utf-8"))
    mem.seek(0)
    return StreamingResponse(mem, media_type="application/zip", headers={"Content-Disposition":"attachment; filename=transliterations.zip"})
