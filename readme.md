Run with:

uvicorn api_fastapi:app --reload --port 8000


Example curl (single target):

curl -F "tgt=DEVANAGARI" -F "file=@input.txt" http://127.0.0.1:8000/transliterate
