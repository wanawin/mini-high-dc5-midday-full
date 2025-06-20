import streamlit as st
from itertools import product, combinations
import os
import pandas as pd
import re

# ==============================
# Inline DC-5 Midday Model Functions
# ==============================
def calculate_seed_sum(seed):
    s = str(seed)
    return sum(int(d) for d in s if d.isdigit())

def shared_digits_count(combo, seed):
    return sum(min(combo.count(d), seed.count(d)) for d in set(combo))

def has_consecutive_run(combo, run_length=4):
    digits = sorted(int(d) for d in combo)
    count = 1
    for i in range(1, len(digits)):
        if digits[i] == digits[i-1] + 1:
            count += 1
            if count >= run_length:
                return True
        else:
            count = 1
    return False

def digit_spread(combo):
    digits = sorted(int(d) for d in combo)
    return digits[-1] - digits[0]

def mirror_digits(combo):
    return {str(9 - int(d)) for d in combo}

# ==============================
# Generate combinations function
# ==============================
def generate_combinations(seed, method="2-digit pair"):
    all_digits = '0123456789'
    combos = set()
    seed_str = str(seed)
    if method == "1-digit":
        for d in seed_str:
            for p in product(all_digits, repeat=4):
                combo = ''.join(sorted(d + ''.join(p)))
                combos.add(combo)
    else:
        pairs = set(''.join(sorted((seed_str[i], seed_str[j])))
                    for i in range(len(seed_str)) for j in range(i+1, len(seed_str)))
        for pair in pairs:
            for p in product(all_digits, repeat=3):
                combo = ''.join(sorted(pair + ''.join(p)))
                combos.add(combo)
    return sorted(combos)

# ==============================
# Core filters: stub and seed intersection
# ==============================
def primary_percentile_pass(combo):
    return True

def core_filters(combo, seed, method="2-digit pair"):
    if not primary_percentile_pass(combo):
        return True
    seed_combos = set(generate_combinations(seed, method=method))
    if combo not in seed_combos:
        return True
    return False

# ==============================
# Load manual filters from external file or upload
# ==============================
def load_manual_filters_from_file(uploaded_file=None,
                                  filepath_txt="manual_filters_full.txt",
                                  filepath_csv="DC5_Midday_Filter_List__With_Descriptions_.csv"):
    raw_lines = []
    filters = []
    def normalize(text):
        text = text.strip()
        if not text:
            return None
        # unify hyphens/dashes
        text = text.replace('—', '-').replace('–', '-')
        # remove leading numbering like "1." or "42)"
        text = re.sub(r'^[0-9]+[\.)]?\s*', '', text)
        return text

    # Debug: list available files
    try:
        cwd_files = os.listdir('.')
        st.debug = getattr(st, 'debug', st.write)
        st.debug(f"Files in cwd: {cwd_files}")
        data_files = os.listdir('/mnt/data') if os.path.exists('/mnt/data') else []
        st.debug(f"Files in /mnt/data: {data_files}")
    except Exception:
        pass

    # Read raw content
    content = None
    if uploaded_file is not None:
        try:
            content = uploaded_file.getvalue().decode('utf-8', errors='ignore')
            st.write(f"Loaded raw manual filters from uploaded file")
        except Exception as e:
            st.warning(f"Failed reading uploaded file: {e}")
    else:
        # Try disk locations
        paths_to_try = [filepath_txt, os.path.join(os.getcwd(), filepath_txt), f"/mnt/data/{filepath_txt}"]
        for path in paths_to_try:
            try:
                if os.path.exists(path):
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    st.write(f"Loaded raw manual filters from {path}")
                    break
            except Exception as e:
                st.warning(f"Failed reading manual filters from {path}: {e}")
    if content is None:
        st.info("No manual filters loaded. Please upload a valid TXT or CSV file or place manual_filters_full.txt in app directory or /mnt/data.")
        return []
    # Split into raw lines
    for line in content.splitlines():
        raw_lines.append(line)
    # Show raw preview for debugging
    st.text_area("Raw manual filter lines", value="\n".join(raw_lines[:50]), height=200)

        # Process lines into blocks: group by blank lines only
    blocks = []
    current = []
    for line in raw_lines:
        nt = normalize(line)
        if nt:
            current.append(nt)
        else:
            if current:
                blocks.append(current)
                current = []
    if current:
        blocks.append(current)

    # Combine each block into single filter text
    for blk in blocks:
        combined = ' '.join(blk)
        filters.append(combined)
    st.write(f"Loaded {len(filters)} manual filter entries (grouped from file)")
    return filters
    blocks = []
    current = []
    header_pattern = re.compile(r'^(Seed Sum|Seed Contains|Mirror Count|V-Trac|Hot Digits|Cold Digits|Type:|Logic:|Action:)', re.IGNORECASE)
    for line in raw_lines:
        nt = normalize(line)
        if nt:
            # If line starts a new filter header and current has content, start new block
            if header_pattern.match(nt) and current:
                blocks.append(current)
                current = [nt]
            else:
                current.append(nt)
        else:
            if current:
                blocks.append(current)
                current = []
    if current:
        blocks.append(current)

    # Combine each block into single filter text
    for blk in blocks:
        combined = ' '.join(blk)
        filters.append(combined)
    st.write(f"Loaded {len(filters)} manual filter entries (grouped from file)")
    return filters

# ==============================
# Helper: implement each filter's logic
# ==============================
def apply_manual_filter(filter_text, combo, seed, hot_digits, cold_digits, due_digits):
    combo_str = combo
    seed_str = str(seed)
    total = sum(int(d) for d in combo_str)
    seed_sum = calculate_seed_sum(seed_str)
    ft = filter_text.lower()
    # Seed Sum rules
    if 'seed sum ≤12' in ft or 'seed sum <=12' in ft:
        if seed_sum <= 12:
            low, high = 12, 25
            if total < low or total > high:
                return True
    if 'seed sum = 13-15' in ft or 'seed sum = 13–15' in ft:
        if 13 <= seed_sum <= 15:
            low, high = 14, 22
            if total < low or total > high:
                return True
    if 'seed sum = 16' in ft:
        if seed_sum == 16:
            low, high = 12, 20
            if total < low or total > high:
                return True
    if 'seed sum = 17-18' in ft or 'seed sum = 17–18' in ft:
        if 17 <= seed_sum <= 18:
            low, high = 11, 26
            if total < low or total > high:
                return True
    if 'seed sum = 19-21' in ft or 'seed sum = 19–21' in ft:
        if 19 <= seed_sum <= 21:
            low, high = 14, 24
            if total < low or total > high:
                return True
    if 'seed sum = 22-23' in ft or 'seed sum = 22–23' in ft:
        if 22 <= seed_sum <= 23:
            low, high = 16, 25
            if total < low or total > high:
                return True
    if 'seed sum = 24-25' in ft or 'seed sum = 24–25' in ft:
        if 24 <= seed_sum <= 25:
            low, high = 19, 25
            if total < low or total > high:
                return True
    if 'seed sum ≥26' in ft or 'seed sum >=26' in ft:
        if seed_sum >= 26:
            low, high = 20, 28
            if total < low or total > high:
                return True
    # Example: Seed Contains logic
    if 'seed contains 2' in ft:
        if '2' in seed_str:
            if not any(d in combo_str for d in ['5','4']):
                return True
    # Additional filter logic can be added here parsing filter_text patterns
    return False

# ==============================
# Trap V3 Ranking Integration
# ==============================
def rank_with_trap_v3(combos, seed):
    try:
        import dc5_trapv3_model as trap_model
        ranked = trap_model.rank_combinations(combos, str(seed))
        return ranked
    except ImportError:
        st.warning("Trap V3 model not available. Ensure `dc5_trapv3_model` is in path and exposes `rank_combinations`.")
        return combos
    except Exception as e:
        st.error(f"Error running Trap V3 ranking: {e}")
        return combos

# ==============================
# Streamlit App
# ==============================
st.title("DC-5 Midday Blind Predictor")
# Sidebar inputs
seed = st.sidebar.text_input("5-digit seed:")
hot_digits = [d for d in st.sidebar.text_input("Hot digits (comma-separated):").replace(' ', '').split(',') if d]
cold_digits = [d for d in st.sidebar.text_input("Cold digits (comma-separated):").replace(' ', '').split(',') if d]
due_digits = [d for d in st.sidebar.text_input("Due digits (comma-separated):").replace(' ', '').split(',') if d]
method = st.sidebar.selectbox("Generation Method:", ["1-digit", "2-digit pair"]) 
enable_trap = st.sidebar.checkbox("Enable Trap V3 Ranking")
# File uploader for manual filters
uploaded = st.sidebar.file_uploader("Upload manual filters file (CSV or TXT)", type=['csv','txt'])

# Load manual filters
manual_filters_list = []
if uploaded is not None or os.path.exists("manual_filters_full.txt") or os.path.exists(f"/mnt/data/manual_filters_full.txt"):
    manual_filters_list = load_manual_filters_from_file(uploaded)

# Generate base pool after core filters
current_pool = []
if seed:
    combos_initial = generate_combinations(seed, method)
    filtered_initial = [c for c in combos_initial if not core_filters(c, seed, method=method)]
    current_pool = filtered_initial.copy()
    if 'original_pool' not in st.session_state or st.session_state.get('seed') != seed or st.session_state.get('method') != method:
        st.session_state.original_pool = current_pool.copy()
        st.session_state.seed = seed
        st.session_state.method = method

# Compute static elimination counts for UI
ranking_sorted = []
if seed and manual_filters_list:
    ranking = []
    for filt in manual_filters_list:
        count_elim = len([c for c in st.session_state.original_pool if apply_manual_filter(filt, c, seed, hot_digits, cold_digits, due_digits)])
        ranking.append((filt, count_elim))
    ranking_sorted = sorted(ranking, key=lambda x: x[1])
else:
    ranking_sorted = [(filt, 0) for filt in manual_filters_list]

st.markdown("## Manual Filters (Least → Most Aggressive)")

if not manual_filters_list:
    st.info("No manual filters loaded. Upload a filter file or ensure manual_filters_full.txt is in app directory or /mnt/data.")

# Compute session_pool by applying selected filters each run
session_pool = st.session_state.get('original_pool', []).copy() if seed else []
for idx, (filt, static_count) in enumerate(ranking_sorted):
    col1, col2 = st.columns([0.85, 0.15])
    key_cb = f"filter_cb_{idx}"
    key_help = f"help_{idx}"
    checkbox_label = f"{filt} — would eliminate {static_count} combos"
    checked = col1.checkbox(checkbox_label, key=key_cb)
    if col2.button("?", key=key_help):
        elim = len([c for c in session_pool if apply_manual_filter(filt, c, seed, hot_digits, cold_digits, due_digits)])
        st.info(f"Filter: {filt}\nSession elimination: {elim} combos")
    if checked and seed:
        session_pool = [c for c in session_pool if not apply_manual_filter(filt, c, seed, hot_digits, cold_digits, due_digits)]

if seed:
    st.session_state.session_pool = session_pool
    st.session_state.original_pool = st.session_state.original_pool

st.markdown(f"**Final Remaining combos after selected manual filters:** {len(st.session_state.session_pool) if seed else 0}")

# Show remaining combos
if seed:
    with st.expander("Show all remaining combinations"):
        if st.session_state.session_pool:
            for combo in st.session_state.session_pool:
                st.write(combo)
        else:
            st.write("No combinations remaining.")

# Trap V3 Ranking
if enable_trap and seed:
    st.markdown("## Trap V3 Ranking")
    ranked_list = rank_with_trap_v3(st.session_state.session_pool, seed)
    if ranked_list:
        st.write("Top combinations by Trap V3:")
        for combo in ranked_list[:20]:
            st.write(combo)
        if len(ranked_list) > 20:
            with st.expander("Show all ranked combinations"):
                for combo in ranked_list:
                    st.write(combo)
    else:
        st.write("No combinations to rank or ranking failed.")
