Run with:

uvicorn api_fastapi:app --reload --port 8000


Example curl (single target):

curl -F "tgt=DEVANAGARI" -F "file=@input.txt" http://127.0.0.1:8000/transliterate
Run:

python app_flask.py
# or use gunicorn etc

django_snippet.md

(If you want to integrate into Django — view example)

# views.py snippet

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from utils_translit import ocr_pdf_bytes, ocr_image_bytes, guess_input_scheme, transliterate_text

@csrf_exempt
def transliterate_view(request):
    if request.method != "POST":
        return JsonResponse({"error":"POST only"}, status=405)
    uploaded = request.FILES.get('file')
    tgt = request.POST.getlist('tgt')
    src = request.POST.get('src','Auto')
    tess_lang = request.POST.get('tess_lang','eng')
    data = uploaded.read()
    # same extraction logic as above...
    # return HttpResponse or FileResponse for zip

Run instructions (local)

Install system dependencies

Ubuntu / Debian:

sudo apt update
sudo apt install -y tesseract-ocr poppler-utils
# optional tesseract languages (e.g., Hindi, Bengali)
sudo apt install -y tesseract-ocr-hin tesseract-ocr-ben


Windows: install Tesseract from https://github.com/tesseract-ocr/tesseract
 and add to PATH. Install Poppler for Windows (for pdf2image).

macOS:

brew install tesseract poppler


Create a virtualenv & install Python deps

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt


Run the Streamlit app

streamlit run app_streamlit.py


Open the URL shown (usually http://localhost:8501
).

Run FastAPI (optional)

uvicorn api_fastapi:app --reload --port 8000


Run Flask (optional)

FLASK_APP=app_flask.py flask run --port 5000

Extra features included / suggested (what I added)

OCR (images & PDFs) via pytesseract + pdf2image

Auto-detect script (Unicode-range heuristic)

Heuristic input-scheme guess (IAST vs ITRANS vs DEVANAGARI/BENGALI etc.)

Manual input-scheme override

Batch processing + ZIP download

Encoding choice for outputs (utf-8, utf-8-sig, latin-1)

Logging panel and progress feedback

FastAPI and Flask endpoints for programmatic usage

Download buttons & previews for results

Robust error handling and fallbacks

Limitations & notes

indic-transliteration excels for Indic (Brahmic) scripts and Roman schemes (ITRANS, IAST, SLP1, VELTHUIS, etc.). It does not support many Semitic or exotic scripts. For those you'd use Aksharamukha — but you asked to use indic-transliteration, so this app focuses on Indic conversions.

OCR quality for Indic scripts requires installing the correct Tesseract language packs (e.g., hin, ben).

Unicode-detection is heuristic. If detection is wrong, use the manual input-scheme override.

For heavy/batch production, run the FastAPI microservice behind a proper ASGI server (uvicorn/gunicorn) and queue jobs.
