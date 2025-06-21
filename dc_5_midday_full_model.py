import streamlit as st
from itertools import product, combinations
import os
import re
import unicodedata

# ==============================
# BOOT CHECKPOINT
# ==============================
st.title("🤪 DC-5 Midday Filter App")
st.success("✅ App loaded: Boot successful.")

# ==============================
# Manual Filter Parsing
# ==============================
def parse_manual_filters_txt(raw_text: str):
    entries = []
    blocks = [blk.strip() for blk in raw_text.strip().split("\n\n") if blk.strip()]
    for blk in blocks:
        lines = [ln.strip() for ln in blk.splitlines() if ln.strip()]
        if len(lines) >= 4:
            name = lines[0]
            type_line = lines[1]
            logic_line = lines[2]
            action_line = lines[3]
            typ = type_line.split(":", 1)[1].strip() if ":" in type_line else type_line
            logic = logic_line.split(":", 1)[1].strip() if ":" in logic_line else logic_line
            action = action_line.split(":", 1)[1].strip() if ":" in action_line else action_line
            entries.append({"name": name, "type": typ, "logic": logic, "action": action})
        else:
            st.warning(f"Skipped manual-filter block (not 4 lines): {blk[:50]}...")
    return entries

# ==============================
# Helper: Normalize and Strip Names
# ==============================
def strip_prefix(raw_name: str) -> str:
    return re.sub(r'^\s*\d+[\.\)]\s*', '', raw_name).strip()

def normalize_name(raw_name: str) -> str:
    s = unicodedata.normalize('NFKC', raw_name)
    s = s.replace('≥', '>=').replace('≤', '<=')
    s = s.replace('\u2265', '>=').replace('\u2264', '<=')
    s = s.replace('→', '->').replace('\u2192', '->')
    s = s.replace('–', '-').replace('—', '-')
    s = s.replace('\u200B', '').replace('\u00A0', ' ')
    s = re.sub(r'\s+', ' ', s)
    return s.strip().lower()

# ==============================
# Debugging Filter Parsing
# ==============================
def debug_build_filter_functions(parsed_filters):
    for pf in parsed_filters:
        raw_name = pf['name']
        stripped = strip_prefix(raw_name)
        name_norm = normalize_name(stripped)
        lower = name_norm.lower()

        st.text(f"RAW name repr:        {repr(raw_name)}")
        st.text(f"STRIPPED name repr:   {repr(stripped)}")
        st.text(f"NORMALIZED name repr: {repr(name_norm)}")

        m_hyphen = bool(re.search(r'seed sum\s*(?:=)?\s*(\d+)\s*-\s*(\d+)', lower))
        m_le     = bool(re.search(r'seed sum\s*(?:<=|≤)\s*(\d+)', lower))
        m_ge     = bool(re.search(r'seed sum\s*(?:>=|≥)\s*(\d+)', lower))
        m_eq     = bool(re.search(r'seed sum\s*=\s*(\d+)', lower)) and not m_hyphen
        m_seed_contains = 'seed contains' in lower and 'winner must contain' in lower

        st.write(f"  Matches hyphen range? {m_hyphen}")
        st.write(f"  Matches <= pattern?  {m_le}")
        st.write(f"  Matches >= pattern?  {m_ge}")
        st.write(f"  Matches = pattern?   {m_eq}")
        st.write(f"  Matches seed-contains pattern? {m_seed_contains}")
        st.write("---")

# ==============================
# Load Manual Filters
# ==============================
manual_txt_path = "manual_filters_full.txt"
if os.path.exists(manual_txt_path):
    raw_txt = open(manual_txt_path, 'r').read()
    st.info(f"Loaded raw manual filters from {manual_txt_path}")
    parsed = parse_manual_filters_txt(raw_txt)
    st.text_area("Raw manual filter lines", raw_txt, height=200)
    st.write(f"Parsed {len(parsed)} manual filter blocks")

    debug_build_filter_functions(parsed)  # DEBUGGING step
else:
    st.error("manual_filters_full.txt not found.")
