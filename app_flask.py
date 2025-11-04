# app_flask.py
from flask import Flask, request, send_file, jsonify
from utils_translit import ocr_image_bytes, ocr_pdf_bytes, guess_input_scheme, transliterate_text
import io, zipfile

app = Flask(__name__)

@app.route("/transliterate", methods=["POST"])
def transliterate():
    if "file" not in request.files:
        return jsonify({"error":"no file"}), 400
    f = request.files["file"]
    tgt = request.form.getlist("tgt")
    src = request.form.get("src", "Auto")
    tess_lang = request.form.get("tess_lang", "eng")
    data = f.read()
    name = f.filename
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
        return jsonify({"error":"no text extracted"}), 400
    src_scheme = src if src != "Auto" else guess_input_scheme(text)
    results = {t: transliterate_text(text, src_scheme, t) for t in tgt}
    if len(tgt) == 1:
        return results[tgt[0]]
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as zf:
        for scheme, content in results.items():
            zf.writestr(f"{name}__{scheme}.txt", content.encode("utf-8"))
    mem.seek(0)
    return send_file(mem, mimetype='application/zip', as_attachment=True, attachment_filename='transliterations.zip')
