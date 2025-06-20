import streamlit as st
from itertools import product, combinations
import os
import pandas as pd

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
    # combo may be string of digits
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
    # Only include combos generated from seed
    seed_combos = set(generate_combinations(seed, method=method))
    if combo not in seed_combos:
        return True
    return False

# ==============================
# Load manual filters from external file
# ==============================
def load_manual_filters_from_file(uploaded_file=None,
                                  filepath_txt="manual_filters_full.txt",
                                  filepath_csv="DC5_Midday_Filter_List__With_Descriptions_.csv"):
    filters = []
    def normalize(text):
        text = text.strip()
        if not text:
            return None
        # Normalize dashes
        text = text.replace('—', '-').replace('–', '-')
        # Remove leading numbering like "1." or "42)"
        import re
        text = re.sub(r'^[0-9]+[\.)]?\s*', '', text)
        return text

    # If uploader provided
    if uploaded_file is not None:
        try:
            name = uploaded_file.name.lower()
            content = uploaded_file.getvalue().decode('utf-8')
            if name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
                col_candidates = [c for c in df.columns if 'filter' in c.lower() or 'name' in c.lower()]
                if col_candidates:
                    for text in df[col_candidates[0]].astype(str).tolist():
                        nt = normalize(text)
                        if nt:
                            filters.append(nt)
                    return filters
            else:
                for line in content.splitlines():
                    nt = normalize(line)
                    if nt:
                        filters.append(nt)
                return filters
        except Exception as e:
            st.warning(f"Failed loading uploaded manual filters: {e}")
    # Try CSV on disk
    # Also check /mnt/data path (Streamlit sandbox)
    paths_to_try = [filepath_csv, filepath_txt, f"/mnt/data/{filepath_csv}", f"/mnt/data/{filepath_txt}"]
    for path in paths_to_try:
        if os.path.exists(path):
            try:
                if path.lower().endswith('.csv'):
                    df = pd.read_csv(path)
                    col_candidates = [c for c in df.columns if 'filter' in c.lower() or 'name' in c.lower()]
                    if col_candidates:
                        for text in df[col_candidates[0]].astype(str).tolist():
                            nt = normalize(text)
                            if nt:
                                filters.append(nt)
                        return filters
                else:
                    with open(path, "r", encoding='utf-8') as f:
                        for line in f:
                            nt = normalize(line)
                            if nt:
                                filters.append(nt)
                    return filters
            except Exception as e:
                st.warning(f"Failed loading manual filters from {path}: {e}")
    # Fallback empty
    if not filters:
        st.warning("No manual filters loaded. Please upload a valid TXT or CSV file containing filter descriptions.")
    return filters

# ==============================
# Helper: implement each filter's logic
# ==============================
def apply_manual_filter(filter_text, combo, seed, hot_digits, cold_digits, due_digits):
    combo_str = combo  # string
    seed_str = str(seed)
    total = sum(int(d) for d in combo_str)
    ft = filter_text.lower()
    import re
    # Example filter implementations:
    if ft.startswith("cold digit trap"):
        return not any(d in combo_str for d in cold_digits)
    if "mirror count" in ft:
        mirror_set = mirror_digits(seed_str)
        return not any(d in mirror_set for d in combo_str)
    if "eliminate triples" in ft or ft.startswith("triple"):
        return any(combo_str.count(d) >= 3 for d in set(combo_str))
    if "eliminate quads" in ft or ft.startswith("quad"):
        return any(combo_str.count(d) >= 4 for d in set(combo_str))
    if "eliminate quints" in ft or ft.startswith("quint"):
        return any(combo_str.count(d) == 5 for d in set(combo_str))
    if ">= 8" in ft or "digits >=8" in ft:
        return sum(1 for d in combo_str if int(d) >= 8) >= 2
    if "all low digits" in ft or "0-3" in ft or "0 to 3" in ft:
        return all(int(d) <= 3 for d in combo_str)
    if "consecutive" in ft and ">=4" in ft:
        return has_consecutive_run(combo_str, run_length=4)
    if "double-doubles only" in ft:
        counts = [combo_str.count(d) for d in set(combo_str)]
        return sorted(counts) == [1,2,2]
    if "prime digit" in ft:
        primes = set(['2','3','5','7'])
        return sum(1 for d in combo_str if d in primes) >= 2
    # Position filters
    mpos = re.search(r'position\s*(\d+)\s*cannot be ([0-9,\s]+)', ft)
    if mpos:
        pos = int(mpos.group(1)) - 1
        bads = [d.strip() for d in mpos.group(2).split(',')]
        if 0 <= pos < len(combo_str) and combo_str[pos] in bads:
            return True
        return False
    # Sum range
    mlt = re.search(r'sum\s*<\s*(\d+)', ft)
    mgt = re.search(r'sum\s*>\s*(\d+)', ft)
    if mlt:
        return total < int(mlt.group(1))
    if mgt:
        return total > int(mgt.group(1))
    # Seed-based sum filters
    if "seed contains 0" in ft and "5" in ft:
        if '0' in seed_str and '5' in seed_str:
            return total < 10 or total > 30
    if "seed contains 0" in ft and "6" in ft:
        if '0' in seed_str and '6' in seed_str:
            return total < 8 or total > 29
    if "seed contains 0" in ft and "7" in ft:
        if '0' in seed_str and '7' in seed_str:
            return total < 8 or total > 28
    # Mirror Sum
    if "mirror sum = combo sum" in ft:
        mirror_sum = sum(int(d) for d in mirror_digits(seed_str))
        return total == mirror_sum
    # If not matched, default: do not eliminate
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
if uploaded is not None or os.path.exists(f"/mnt/data/manual_filters_full.txt"):
    manual_filters_list = load_manual_filters_from_file(uploaded)

# Generate base pool after core filters
current_pool = []
if seed:
    combos_initial = generate_combinations(seed, method)
    filtered_initial = [c for c in combos_initial if not core_filters(c, seed, method=method)]
    current_pool = filtered_initial.copy()

# Compute static elimination counts
ranking_sorted = []
if seed:
    ranking = []
    for filt in manual_filters_list:
        count_elim = len([c for c in current_pool if apply_manual_filter(filt, c, seed, hot_digits, cold_digits, due_digits)])
        ranking.append((filt, count_elim))
    ranking_sorted = sorted(ranking, key=lambda x: x[1])
else:
    ranking_sorted = [(filt, 0) for filt in manual_filters_list]

st.markdown("## Manual Filters (Least → Most Aggressive)")

# Use session state for pool persistence
if 'session_pool' not in st.session_state:
    st.session_state.session_pool = current_pool.copy() if seed else []
if seed:
    st.session_state.session_pool = current_pool.copy()

if not manual_filters_list:
    st.info("No manual filters loaded. Upload a filter file or ensure manual_filters_full.txt is in /mnt/data.")

for idx, (filt, static_count) in enumerate(ranking_sorted):
    col1, col2 = st.columns([0.85, 0.15])
    key_cb = f"filter_cb_{idx}"
    key_help = f"help_{idx}"
    checkbox_label = f"{filt} — would eliminate {static_count} combos"
    checked = col1.checkbox(checkbox_label, key=key_cb)
    if col2.button("?", key=key_help):
        st.info(f"Filter: {filt}\nSession elimination: {len([c for c in st.session_state.session_pool if apply_manual_filter(filt, c, seed, hot_digits, cold_digits, due_digits)])} combos")
    if checked and seed:
        to_remove = [c for c in st.session_state.session_pool if apply_manual_filter(filt, c, seed, hot_digits, cold_digits, due_digits)]
        eliminated_count = len(to_remove)
        st.session_state.session_pool = [c for c in st.session_state.session_pool if c not in to_remove]
        col1.write(f"Eliminated {eliminated_count} combos; Remaining combos: {len(st.session_state.session_pool)}")

st.markdown(f"**Final Remaining combos after selected manual filters:** {len(st.session_state.session_pool)}")

# Show remaining combos
if seed:
    with st.expander("Show all remaining combinations"):
        if st.session_state.session_pool:
            for combo in st.session_state.session_pool:
                st.write(combo)
        else:
            st.write("No combinations remaining.")

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
