import streamlit as st
from itertools import product, combinations
import os
import re

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
# Load Manual Filters
# ==============================
manual_txt_path = "manual_filters_full.txt"
if os.path.exists(manual_txt_path):
    raw_txt = open(manual_txt_path, 'r').read()
    st.info(f"Loaded raw manual filters from {manual_txt_path}")
    parsed = parse_manual_filters_txt(raw_txt)
    st.text_area("Raw manual filter lines", raw_txt, height=200)
    st.write(f"Parsed {len(parsed)} manual filter blocks")

    # Import dynamic builder
    from dc5_manual_filter_ranked_list import build_filter_functions
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
