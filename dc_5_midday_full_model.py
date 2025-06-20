import streamlit as st
from itertools import product, combinations
import os
import re

# ==============================
# BOOT CHECKPOINT
# ==============================
st.title("🧪 DC-5 Midday Filter App")
st.success("✅ App loaded: Boot successful.")

# ==============================
# Inline DC-5 Midday Model Functions
# ==============================
# ... (rest unchanged)

# ==============================
# Load manual filters with safe guards
# ==============================
def load_manual_filters_from_file(uploaded_file=None, filepath_txt="manual_filters_degrouped.txt"):
    content = None
    if uploaded_file is not None:
        try:
            content = uploaded_file.read().decode('utf-8', errors='ignore')
            st.info("Loaded raw manual filters from uploaded file")
        except Exception as e:
            st.warning(f"Failed reading uploaded file: {e}")
    else:
        paths_to_try = [filepath_txt, os.path.join(os.getcwd(), filepath_txt), f"/mnt/data/{filepath_txt}"]
        for path in paths_to_try:
            if os.path.exists(path):
                if "full" in os.path.basename(path).lower():
                    st.info(f"Skipped grouped file: {path}")
                    continue
                try:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    st.info(f"Loaded raw manual filters from {path}")
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
        st.info(f"Parsed {len(parsed)} manual filter blocks")
        st.text_area("Preview manual filter names", value="\n".join(p['name'] for p in parsed[:20]), height=200)
        return parsed
    except Exception as e:
        st.error(f"Error parsing manual filters: {e}")
        return []

# ==============================
# Top-Level Error Guard for Main Logic
# ==============================
try:
    seed = st.sidebar.text_input("5-digit seed:")
    hot_digits = [d for d in st.sidebar.text_input("Hot digits (comma-separated):").replace(' ', '').split(',') if d]
    cold_digits = [d for d in st.sidebar.text_input("Cold digits (comma-separated):").replace(' ', '').split(',') if d]
    due_digits = [d for d in st.sidebar.text_input("Due digits (comma-separated):").replace(' ', '').split(',') if d]
    method = st.sidebar.selectbox("Generation Method:", ["1-digit", "2-digit pair"]) 
    enable_trap = st.sidebar.checkbox("Enable Trap V3 Ranking")
    uploaded = st.sidebar.file_uploader("Upload manual filters file (TXT degrouped)", type=['txt'])

    parsed_filters = load_manual_filters_from_file(uploaded)
    filter_entries = build_filter_functions(parsed_filters)

    if seed:
        combos_initial = generate_combinations(seed, method)
        filtered_initial = [c for c in combos_initial if not core_filters(c, seed, method=method)]
        st.session_state['original_pool'] = filtered_initial.copy()
        st.success(f"Generated {len(filtered_initial)} combos after core filters.")
    else:
        st.warning("Enter a seed to generate combos.")

except Exception as boot_err:
    st.error(f"🚨 Top-level app crash: {boot_err}")
