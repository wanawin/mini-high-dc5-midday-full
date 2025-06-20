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
# Core filters: percentile stub and seed intersection
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
        # Remove leading numbering
        if text and text[0].isdigit():
            parts = text.split('.', 1)
            if len(parts) == 2 and parts[0].isdigit():
                text = parts[1].strip()
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
    if os.path.exists(filepath_csv):
        try:
            df = pd.read_csv(filepath_csv)
            col_candidates = [c for c in df.columns if 'filter' in c.lower() or 'name' in c.lower()]
            if col_candidates:
                for text in df[col_candidates[0]].astype(str).tolist():
                    nt = normalize(text)
                    if nt:
                        filters.append(nt)
                return filters
        except Exception as e:
            st.warning(f"Failed loading CSV manual filters: {e}")
    # Try TXT on disk
    if os.path.exists(filepath_txt):
        try:
            with open(filepath_txt, "r") as f:
                for line in f:
                    nt = normalize(line)
                    if nt:
                        filters.append(nt)
            return filters
        except Exception as e:
            st.warning(f"Error loading manual filters from txt: {e}")
    # Fallback empty
    return []

# ==============================
# Helper: implement each filter's logic
# ==============================
def apply_manual_filter(filter_text, combo, seed, hot_digits, cold_digits, due_digits):
    combo_str = ''.join(combo)
    seed_str = str(seed)
    total = sum(int(d) for d in combo_str)
    ft = filter_text.lower()
    # Cold Digit Trap
    if ft.startswith("cold digit trap"):
        for d in cold_digits:
            if d and d in combo_str:
                return False
        return True
    # Mirror Count = 0
    if ft.startswith("mirror count"):
        mirror_set = mirror_digits(seed_str)
        for d in combo_str:
            if d in mirror_set:
                return False
        return True
    # Sum range filters: identify patterns
    import re
    # Example: "sum < x or > y"
    m = re.search(r'sum\s*<\s*(\d+)|sum\s*>\s*(\d+)', filter_text)
    if 'sum' in ft and m:
        # Fallback: skip complex
        pass
    # Additional cases (position, repeating, etc.)
    # TODO: extend as needed for all filter rules
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
t_uploaded = st.sidebar.file_uploader("Upload manual filters file (CSV or TXT)", type=['csv','txt'])

# Load manual filters
manual_filters_list = load_manual_filters_from_file(t_uploaded)

# Generate base pool after core filters
current_pool = []
if seed:
    combos_initial = generate_combinations(seed, method)
    filtered_initial = [c for c in combos_initial if not core_filters(c, seed, method=method)]
    current_pool = filtered_initial.copy()

# Compute static elimination counts for ranking
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

session_pool = current_pool.copy() if seed else []

def display_filter_help(filt, session_pool):
    if seed:
        current_to_remove = [c for c in session_pool if apply_manual_filter(filt, c, seed, hot_digits, cold_digits, due_digits)]
        st.info(f"Filter: {filt}\nEliminates {len(current_to_remove)} combinations in this session")

for idx, (filt, static_count) in enumerate(ranking_sorted):
    col1, col2 = st.columns([0.85, 0.15])
    key_cb = f"filter_cb_{idx}"
    key_help = f"help_{idx}"
    checkbox_label = f"{filt} — would eliminate {static_count} combos"
    checked = col1.checkbox(checkbox_label, key=key_cb)
    if col2.button("?", key=key_help):
        display_filter_help(filt, session_pool)
    if checked and seed:
        to_remove = [c for c in session_pool if apply_manual_filter(filt, c, seed, hot_digits, cold_digits, due_digits)]
        eliminated_count = len(to_remove)
        session_pool = [c for c in session_pool if c not in to_remove]
        col1.write(f"Eliminated {eliminated_count} combos; Remaining combos: {len(session_pool)}")

st.markdown(f"**Final Remaining combos after selected manual filters:** {len(session_pool)}")

# Show remaining combos
if seed:
    with st.expander("Show all remaining combinations"):
        if session_pool:
            for combo in session_pool:
                st.write(combo)
        else:
            st.write("No combinations remaining.")

if enable_trap and seed:
    st.markdown("## Trap V3 Ranking")
    ranked_list = rank_with_trap_v3(session_pool, seed)
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
# Core filters: percentile stub and seed intersection
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
        # Remove leading numbering
        if text and text[0].isdigit():
            parts = text.split('.', 1)
            if len(parts) == 2 and parts[0].isdigit():
                text = parts[1].strip()
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
    if os.path.exists(filepath_csv):
        try:
            df = pd.read_csv(filepath_csv)
            col_candidates = [c for c in df.columns if 'filter' in c.lower() or 'name' in c.lower()]
            if col_candidates:
                for text in df[col_candidates[0]].astype(str).tolist():
                    nt = normalize(text)
                    if nt:
                        filters.append(nt)
                return filters
        except Exception as e:
            st.warning(f"Failed loading CSV manual filters: {e}")
    # Try TXT on disk
    if os.path.exists(filepath_txt):
        try:
            with open(filepath_txt, "r") as f:
                for line in f:
                    nt = normalize(line)
                    if nt:
                        filters.append(nt)
            return filters
        except Exception as e:
            st.warning(f"Error loading manual filters from txt: {e}")
    # Fallback empty
    return []

# ==============================
# Helper: implement each filter's logic
# ==============================
def apply_manual_filter(filter_text, combo, seed, hot_digits, cold_digits, due_digits):
    combo_str = ''.join(combo)
    seed_str = str(seed)
    total = sum(int(d) for d in combo_str)
    ft = filter_text.lower()
    # Cold Digit Trap
    if ft.startswith("cold digit trap"):
        for d in cold_digits:
            if d and d in combo_str:
                return False
        return True
    # Mirror Count = 0
    if ft.startswith("mirror count"):
        mirror_set = mirror_digits(seed_str)
        for d in combo_str:
            if d in mirror_set:
                return False
        return True
    # Sum range filters: identify patterns
    import re
    # Example: "sum < x or > y"
    m = re.search(r'sum\s*<\s*(\d+)|sum\s*>\s*(\d+)', filter_text)
    if 'sum' in ft and m:
        # Fallback: skip complex
        pass
    # Additional cases (position, repeating, etc.)
    # TODO: extend as needed for all filter rules
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
t_uploaded = st.sidebar.file_uploader("Upload manual filters file (CSV or TXT)", type=['csv','txt'])

# Load manual filters
manual_filters_list = load_manual_filters_from_file(t_uploaded)

# Generate base pool after core filters
current_pool = []
if seed:
    combos_initial = generate_combinations(seed, method)
    filtered_initial = [c for c in combos_initial if not core_filters(c, seed, method=method)]
    current_pool = filtered_initial.copy()

# Compute static elimination counts for ranking
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

session_pool = current_pool.copy() if seed else []

def display_filter_help(filt, session_pool):
    if seed:
        current_to_remove = [c for c in session_pool if apply_manual_filter(filt, c, seed, hot_digits, cold_digits, due_digits)]
        st.info(f"Filter: {filt}\nEliminates {len(current_to_remove)} combinations in this session")

for idx, (filt, static_count) in enumerate(ranking_sorted):
    col1, col2 = st.columns([0.85, 0.15])
    key_cb = f"filter_cb_{idx}"
    key_help = f"help_{idx}"
    checkbox_label = f"{filt} — would eliminate {static_count} combos"
    checked = col1.checkbox(checkbox_label, key=key_cb)
    if col2.button("?", key=key_help):
        display_filter_help(filt, session_pool)
    if checked and seed:
        to_remove = [c for c in session_pool if apply_manual_filter(filt, c, seed, hot_digits, cold_digits, due_digits)]
        eliminated_count = len(to_remove)
        session_pool = [c for c in session_pool if c not in to_remove]
        col1.write(f"Eliminated {eliminated_count} combos; Remaining combos: {len(session_pool)}")

st.markdown(f"**Final Remaining combos after selected manual filters:** {len(session_pool)}")

# Show remaining combos
if seed:
    with st.expander("Show all remaining combinations"):
        if session_pool:
            for combo in session_pool:
                st.write(combo)
        else:
            st.write("No combinations remaining.")

if enable_trap and seed:
    st.markdown("## Trap V3 Ranking")
    ranked_list = rank_with_trap_v3(session_pool, seed)
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
