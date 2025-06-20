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
    s = s.replace('≥', '>=').replace('≤', '<=').replace('→', '->')
    s = s.replace('–', '-').replace('—', '-')
    s = s.replace(',', '').lower()
    s = re.sub(r'\s+', ' ', s)
    return s.strip()

# ==============================
# Real Filter Functions
# ==============================
def seed_sum_range_filter(min_sum, max_sum):
    def filter_fn(combos, seed=None, seed_sum=None):
        kept, removed = [], []
        for combo in combos:
            s = sum(int(d) for d in combo)
            (kept if min_sum <= s <= max_sum else removed).append(combo)
        return kept, removed
    return filter_fn

def must_contain_filter(required_digits):
    def filter_fn(combos, seed=None, seed_sum=None):
        kept, removed = [], []
        for combo in combos:
            (kept if any(d in combo for d in required_digits) else removed).append(combo)
        return kept, removed
    return filter_fn

# ==============================
# Manual Filter Builder (Ranked)
# ==============================
def build_filter_functions(parsed_filters):
    ranked = [
        ("01. Seed Sum <= 12", seed_sum_range_filter(12, 25)),
        ("02. Seed Sum = 13-15", seed_sum_range_filter(14, 22)),
        ("03. Seed Sum = 16", seed_sum_range_filter(12, 20)),
        ("04. Seed Sum = 17-18", seed_sum_range_filter(11, 26)),
        ("05. Seed Sum = 19-21", seed_sum_range_filter(14, 24)),
        ("06. Seed Sum = 22-23", seed_sum_range_filter(16, 25)),
        ("07. Seed Sum = 24-25", seed_sum_range_filter(19, 25)),
        ("08. Seed Sum >= 26", seed_sum_range_filter(20, 28)),
        ("09. Seed Contains 2 -> Winner Must Contain 5 or 4", must_contain_filter("54")),
        ("10. Seed Contains 1 -> Winner Must Contain 2, 3, or 4", must_contain_filter("234")),
        ("11. Seed Contains 0 -> Winner Must Contain 1, 2, or 3", must_contain_filter("123")),
    ]

    fns = []
    for name, fn in ranked:
        match_found = False
        norm_ranked = normalize_name(name)
        for pf in parsed_filters:
            norm_pf = normalize_name(pf['name'])
            if norm_pf in norm_ranked or norm_ranked in norm_pf:
                fns.append({"name": name, "fn": fn, "descr": pf.get('logic', '')})
                match_found = True
                break
        if not match_found:
            st.warning(f"No function defined for manual filter: '{name}'")
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
