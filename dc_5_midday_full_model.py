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
# Load Manual Filters
# ==============================
manual_txt_path = "manual_filters_full.txt"
if os.path.exists(manual_txt_path):
    raw_txt = open(manual_txt_path, 'r').read()
    st.info(f"Loaded raw manual filters from {manual_txt_path}")
    parsed = parse_manual_filters_txt(raw_txt)
    st.text_area("Raw manual filter lines", raw_txt, height=200)
    st.write(f"Parsed {len(parsed)} manual filter blocks")

    # ==============================
    # Render Parsed Filters as Actionable Toggles
    # ==============================
    st.markdown("### 🎯 Manual Filter Selection")

    filter_types = {
        "hyphen": [],
        "<=" : [],
        ">=" : [],
        "="  : [],
        "seed→winner": [],
        "unknown": []
    }

    for pf in parsed:
        raw_name = pf['name']
        stripped = strip_prefix(raw_name)
        norm = normalize_name(stripped)
        lower = norm.lower()

        m_hyphen = bool(re.search(r'seed sum\s*(?:=)?\s*(\d+)\s*-\s*(\d+)', lower))
        m_le     = bool(re.search(r'seed sum\s*(?:<=|≤)\s*(\d+)', lower))
        m_ge     = bool(re.search(r'seed sum\s*(?:>=|≥)\s*(\d+)', lower))
        m_eq     = bool(re.search(r'seed sum\s*=\s*(\d+)', lower)) and not m_hyphen
        m_seed_contains = 'seed contains' in lower and 'winner must contain' in lower

        if m_hyphen:
            filter_types["hyphen"].append(pf)
        elif m_le:
            filter_types["<="].append(pf)
        elif m_ge:
            filter_types[">="] .append(pf)
        elif m_eq:
            filter_types["="] .append(pf)
        elif m_seed_contains:
            filter_types["seed→winner"].append(pf)
        else:
            filter_types["unknown"].append(pf)

    # ==============================
    # Show Filters Grouped by Type
    # ==============================
    for group, flist in filter_types.items():
        if not flist:
            continue
        st.markdown(f"#### 🧮 Filter Type: `{group}` ({len(flist)} filters)")
        for f in flist:
            label = strip_prefix(f['name'])
            key = f"filter_{normalize_name(label)}"
            st.checkbox(label, value=False, key=key)
else:
    st.error("manual_filters_full.txt not found.")
