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
# Helper: Normalize Names
# ==============================
def normalize_name(raw_name: str) -> str:
    s = unicodedata.normalize('NFKC', raw_name)
    s = s.replace('≥', '>=').replace('≤', '<=')
    s = s.replace('→', '->')
    s = s.replace('–', '-').replace('—', '-')
    s = re.sub(r'\s+', ' ', s)
    return s.strip()

# ==============================
# Real Filter Functions
# ==============================
def seed_sum_range_filter(min_sum, max_sum):
    def filter_fn(combos, seed=None, seed_sum=None):
        kept = []
        removed = []
        for combo in combos:
            s = sum(int(d) for d in combo)
            if min_sum <= s <= max_sum:
                kept.append(combo)
            else:
                removed.append(combo)
        return kept, removed
    return filter_fn

def must_contain_filter(required_digits):
    def filter_fn(combos, seed=None, seed_sum=None):
        kept = []
        removed = []
        for combo in combos:
            if any(d in combo for d in required_digits):
                kept.append(combo)
            else:
                removed.append(combo)
        return kept, removed
    return filter_fn

# ==============================
# Manual Filter Builder
# ==============================
def build_filter_functions(parsed_filters):
    fns = []
    for pf in parsed_filters:
        raw_name = pf['name'].strip()
        logic = pf.get('logic','')
        action = pf.get('action','')
        name_norm = normalize_name(raw_name)
        lower = name_norm.lower()

        if "seed sum <= 12" in lower:
            fn = seed_sum_range_filter(12, 25)
            fns.append({'name': raw_name, 'fn': fn, 'descr': logic})
            continue

        if "seed sum = 13-15" in lower:
            fn = seed_sum_range_filter(14, 22)
            fns.append({'name': raw_name, 'fn': fn, 'descr': logic})
            continue

        if "seed contains 1" in lower and "winner must contain" in lower:
            fn = must_contain_filter("234")
            fns.append({'name': raw_name, 'fn': fn, 'descr': logic})
            continue

        st.warning(f"No function defined for manual filter: '{raw_name}'")
    return fns

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

    filter_functions = build_filter_functions(parsed)
    st.write("Preview manual filter names", [f['name'] for f in filter_functions])

    seed_input = st.text_input("Enter Seed (5 digits, optional)")
    seed_sum = sum(int(d) for d in seed_input) if seed_input.isdigit() and len(seed_input) == 5 else None

    uploaded_file = st.file_uploader("Upload 5-digit combos (1 per line)", type=["txt"])
    combo_list = []
    if uploaded_file:
        combo_list = [ln.strip() for ln in uploaded_file.read().decode("utf-8").splitlines() if ln.strip()]
    elif st.button("Use Example Combos"):
        combo_list = ["12345", "13579", "11111", "98765", "45678", "22222"]

    if combo_list:
        st.write(f"Loaded {len(combo_list)} combinations.")
        remaining = combo_list[:]
        total_removed = 0
        for filt in filter_functions:
            if st.checkbox(f"Apply: {filt['name']}", value=True):
                remaining, removed = filt['fn'](remaining, seed=seed_input, seed_sum=seed_sum)
                st.write(f"Removed by '{filt['name']}': {len(removed)}")
                total_removed += len(removed)
        st.success(f"Final Count: {len(remaining)} combos (Removed: {total_removed})")
        st.download_button("Download Final Combos", "\n".join(remaining), file_name="filtered_combos.txt")
else:
    st.error("manual_filters_full.txt not found.")
