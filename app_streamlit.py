# app_streamlit.py
import streamlit as st
from utils_translit import (
    ocr_image_bytes, ocr_pdf_bytes, detect_script, guess_input_scheme,
    transliterate_text, batch_transliterate_filetexts, SANSCRIPT_MAP
)
from io import BytesIO
import os
from typing import List, Dict
import tempfile

st.set_page_config(page_title="Indic Transliterator (indic-transliteration) + OCR", layout="wide")
st.title("Indic Transliterator + OCR — Streamlit")
st.markdown("""
Upload text / PDF / image files. The app OCRs (if needed), auto-detects script, 
guesses input scheme, and transliterates using **indic-transliteration**.  
Supports batch files and ZIP download.
""")

# Sidebar settings
st.sidebar.header("Settings")
tess_lang = st.sidebar.text_input("Tesseract language code (for OCR)", value="eng")
encoding_choice = st.sidebar.selectbox("Output file encoding", options=["utf-8", "utf-8-sig", "latin-1"], index=0)
show_logs = st.sidebar.checkbox("Show logs", value=True)

# Target schemes offered (subset of SANSCRIPT_MAP for UI clarity)
COMMON_TARGETS = ["DEVANAGARI", "BENGALI", "GUJARATI", "ORIYA", "TAMIL", "TELUGU", "KANNADA", "MALAYALAM", "IAST", "ITRANS", "SLP1", "VELTHUIS"]

uploaded_files = st.file_uploader("Upload one or more files (txt, pdf, png, jpg, jpeg, tiff)", type=["txt", "pdf", "png", "jpg", "jpeg", "tiff"], accept_multiple_files=True)

manual_src_scheme = st.selectbox("Manual input scheme override (leave 'Auto' for heuristic)", ["Auto"] + sorted(list(SANSCRIPT_MAP.keys())))
targets = st.multiselect("Select target schemes", options=COMMON_TARGETS, default=["DEVANAGARI", "BENGALI"])

if uploaded_files:
    file_texts: Dict[str, str] = {}
    logs = []
    for f in uploaded_files:
        name = f.name
        data = f.read()
        text = ""
        try:
            if name.lower().endswith(".txt"):
                # Try decode utf-8 then fallback
                try:
                    text = data.decode("utf-8")
                except:
                    text = data.decode("latin-1")
            elif name.lower().endswith(".pdf"):
                st.info(f"Performing OCR on PDF: {name}")
                text = ocr_pdf_bytes(data, tesseract_lang=tess_lang)
            else:
                st.info(f"Performing OCR on image: {name}")
                text = ocr_image_bytes(data, tesseract_lang=tess_lang)
        except Exception as e:
            logs.append(f"Error processing {name}: {e}")
            text = ""

        file_texts[name] = text
        logs.append(f"Processed {name}, {len(text)} chars extracted")

    # Display previews and detection
    for fname, txt in file_texts.items():
        st.subheader(f"File: {fname}")
        st.write(f"Extracted chars: {len(txt)}")
        if txt.strip():
            detected_script = detect_script(txt)
            guessed_scheme = guess_input_scheme(txt) if manual_src_scheme == "Auto" else manual_src_scheme
            st.write(f"Detected script (heuristic): **{detected_script}**")
            st.write(f"Input scheme used for transliteration: **{guessed_scheme}**")
            st.code(txt[:2000])
        else:
            st.warning("No text found or OCR failed for this file.")

    if st.button("Transliterate & Download"):
        if not targets:
            st.error("Choose at least one target scheme.")
        else:
            # Create outputs and offer downloads
            # Determine single src_scheme if all files are same type; else use user override or guess per-file
            src_scheme_global = None
            if manual_src_scheme != "Auto":
                src_scheme_global = manual_src_scheme

            # Prepare per-file transliterations
            outputs = {}
            for fname, txt in file_texts.items():
                if not txt.strip():
                    outputs[fname] = {t: "" for t in targets}
                    continue
                src_scheme = src_scheme_global if src_scheme_global else guess_input_scheme(txt)
                outputs[fname] = {}
                for tgt in targets:
                    try:
                        out = transliterate_text(txt, src_scheme, tgt)
                    except Exception as e:
                        out = f"[ERROR] {e}"
                    outputs[fname][tgt] = out

            # If single file & few targets -> offer direct download buttons
            if len(outputs) == 1 and len(targets) <= 4:
                fname = list(outputs.keys())[0]
                for tgt in targets:
                    txt = outputs[fname][tgt]
                    st.markdown(f"**{fname} → {tgt}**")
                    st.text_area(f"preview_{fname}_{tgt}", value=txt[:20000], height=200)
                    st.download_button(f"Download {fname}__{tgt}.txt", data=txt.encode(encoding_choice), file_name=f"{fname}__{tgt}.txt", mime="text/plain")
            else:
                # Create zip
                zip_bytes = batch_transliterate_filetexts({fn: "\n".join(list(map(str, outputs[fn].values()))) if False else file_texts[fn] for fn in outputs}, src_scheme if src_scheme_global else "ITRANS", targets)
                # Note: Because batch_transliterate_filetexts expects original file_texts, for accurate naming we re-run batch_transliterate properly
                # Build a proper zip with transliterated contents
                import zipfile, io
                buffer = io.BytesIO()
                with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                    for fname, tdict in outputs.items():
                        for tgt, content in tdict.items():
                            outname = f"{os.path.splitext(fname)[0]}__{tgt}.txt"
                            zf.writestr(outname, content.encode(encoding_choice))
                buffer.seek(0)
                st.download_button("Download all outputs (ZIP)", data=buffer, file_name="transliterations.zip", mime="application/zip")
            st.success("Transliteration completed.")

    if show_logs:
        st.sidebar.subheader("Logs")
        st.sidebar.write("\n".join(logs))

st.sidebar.markdown("---")
st.sidebar.markdown("Tips:\n- For better OCR on Indic scripts install tesseract language packs (e.g., hin, ben).\n- If results look wrong, try changing the input scheme override.")
