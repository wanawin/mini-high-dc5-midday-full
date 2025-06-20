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
# Manual Filter Builder (Ranked, Dynamic)
# ==============================
def build_filter_functions(parsed_filters):
    fns = []
    for pf in parsed_filters:
        raw_name = pf['name'].strip()
        logic = pf.get('logic', '')
        action = pf.get('action', '')
        norm = normalize_name(raw_name)

        # Match seed sum filters
        m_range = re.search(r'seed sum\s*=\s*(\d+)\s*-\s*(\d+)', norm)
        m_le = re.search(r'seed sum\s*<=\s*(\d+)', norm)
        m_ge = re.search(r'seed sum\s*>=\s*(\d+)', norm)

        if m_range or m_le or m_ge:
            seed_min = int(m_range.group(1)) if m_range else (int(m_ge.group(1)) if m_ge else None)
            seed_max = int(m_range.group(2)) if m_range else (int(m_le.group(1)) if m_le else None)

            low, high = None, None
            m_action = re.search(r'between\s*(\d+)\s*(?:-|and)\s*(\d+)', action)
            if m_action:
                low, high = int(m_action.group(1)), int(m_action.group(2))
            elif 'sum <=' in action or 'sum ≤' in action:
                high = int(re.search(r'sum\s*(?:<=|≤)\s*(\d+)', action).group(1))
            elif 'sum >=' in action or 'sum ≥' in action:
                low = int(re.search(r'sum\s*(?:>=|≥)\s*(\d+)', action).group(1))

            def dynamic_range_filter(seed_sum_min, seed_sum_max, low, high):
                def fn(combos, seed=None, seed_sum=None):
                    if seed_sum is None:
                        return combos, []
                    if seed_sum_min and seed_sum < seed_sum_min:
                        return combos, []
                    if seed_sum_max and seed_sum > seed_sum_max:
                        return combos, []
                    kept, removed = [], []
                    for c in combos:
                        s = sum(int(d) for d in c)
                        (kept if (low or 0) <= s <= (high or 99) else removed).append(c)
                    return kept, removed
                return fn

            fns.append({"name": raw_name, "fn": dynamic_range_filter(seed_min, seed_max, low, high), "descr": logic})
            continue

        # Match Seed Contains → Winner Must Contain
        m_seed = re.search(r'seed contains\s*(\d)', norm)
        m_req = re.findall(r'winner must contain\s*([\d\sorand]+)', norm)
        if m_seed and m_req:
            sd = m_seed.group(1)
            req_digits = re.findall(r'\d', ' '.join(m_req))
            def must_contain_logic(sd, reqs):
                def fn(combos, seed=None, **kwargs):
                    if seed and sd in seed:
                        kept, removed = [], []
                        for c in combos:
                            (kept if any(d in c for d in reqs) else removed).append(c)
                        return kept, removed
                    return combos, []
                return fn
            fns.append({"name": raw_name, "fn": must_contain_logic(sd, req_digits), "descr": logic})
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
