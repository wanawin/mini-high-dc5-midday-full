import streamlit as st
from itertools import product, combinations
import os
import re

# ==============================
# Inline DC-5 Midday Model Functions
# ==============================
# ... [rest of the code unchanged for brevity] ...

# ==============================
# Load manual filters from external file or upload (with grouped file skip logic)
# ==============================
def load_manual_filters_from_file(uploaded_file=None, filepath_txt="manual_filters_degrouped.txt"):
    content = None
    if uploaded_file is not None:
        try:
            content = uploaded_file.read().decode('utf-8', errors='ignore')
            st.write("Loaded raw manual filters from uploaded file")
        except Exception as e:
            st.warning(f"Failed reading uploaded file: {e}")
    else:
        paths_to_try = [filepath_txt, os.path.join(os.getcwd(), filepath_txt), f"/mnt/data/{filepath_txt}"]
        for path in paths_to_try:
            if os.path.exists(path):
                # Auto-ignore grouped files
                if "full" in os.path.basename(path).lower():
                    st.info(f"Skipped grouped file: {path}")
                    continue
                try:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    st.write(f"Loaded raw manual filters from {path}")
                    break
                except Exception as e:
                    st.warning(f"Failed reading manual filters from {path}: {e}")
    if content is None:
        st.info("No manual filters loaded. Upload TXT or place manual_filters_degrouped.txt in app directory.")
        return []
    try:
        raw_lines = content.splitlines()
        st.text_area("Raw manual filter lines", value="\n".join(raw_lines[:50]), height=200)
        parsed = parse_manual_filters_txt(content)
        st.write(f"Parsed {len(parsed)} manual filter blocks")
        st.text_area("Preview manual filter names", value="\n".join(p['name'] for p in parsed[:20]), height=200)
        return parsed
    except Exception as e:
        st.error(f"Error parsing manual filters: {e}")
        return []
