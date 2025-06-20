import streamlit as st
from itertools import product, combinations
import os
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

def mirror_digits(seed):
    return {str(9 - int(d)) for d in str(seed) if d.isdigit()}

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
    # Placeholder: implement actual percentile logic if available
    return True

def core_filters(combo, seed, method="2-digit pair"):
    if not primary_percentile_pass(combo):
        return True
    seed_combos = set(generate_combinations(seed, method=method))
    if combo not in seed_combos:
        return True
    return False

# ==============================
# Parse manual filters TXT
# ==============================
def parse_manual_filters_txt(raw_text: str):
    entries = []
    # Split into blocks separated by blank lines
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
# Filter function factories
# ==============================
def make_conditional_sum_range_filter(seed_sum_min=None, seed_sum_max=None, low=None, high=None):
    def filter_fn(combo_list, seed_sum=None, **kwargs):
        if seed_sum is None:
            return combo_list, []
        if seed_sum_min is not None and seed_sum < seed_sum_min:
            return combo_list, []
        if seed_sum_max is not None and seed_sum > seed_sum_max:
            return combo_list, []
        keep, removed = [], []
        for combo in combo_list:
            s = sum(int(d) for d in combo)
            if (low is not None and s < low) or (high is not None and s > high):
                removed.append(combo)
            else:
                keep.append(combo)
        return keep, removed
    return filter_fn

def make_mirror_zero_filter(mirror_set):
    def filter_fn(combo_list, **kwargs):
        if not mirror_set:
            return combo_list, []
        keep, removed = [], []
        for combo in combo_list:
            if any(d in mirror_set for d in combo):
                keep.append(combo)
            else:
                removed.append(combo)
        return keep, removed
    return filter_fn

def make_position_forbid_filter(pos, forbid_digits):
    def filter_fn(combo_list, **kwargs):
        keep, removed = [], []
        for combo in combo_list:
            if combo[pos-1] in forbid_digits:
                removed.append(combo)
            else:
                keep.append(combo)
        return keep, removed
    return filter_fn

# Extend with additional factories as needed per filter patterns

# ==============================
# Build filter functions from parsed entries
# ==============================
def build_filter_functions(parsed_filters):
    fns = []
    for pf in parsed_filters:
        name = pf['name']
        logic = pf['logic']
        action = pf['action']
        lower_name = name.lower()
        # Seed Sum filters
        m_seed = re.search(r'seed sum\s*[≤<=]?\s*(\d+)(?:[\-–](\d+))?', lower_name)
        if m_seed:
            if m_seed.group(2):
                smin = int(m_seed.group(1)); smax = int(m_seed.group(2))
            else:
                val = int(m_seed.group(1))
                if '≤' in name or '<=' in lower_name:
                    smin = None; smax = val
                else:
                    smin = val; smax = val
            lt = re.search(r'sum\s*<\s*(\d+)', action)
            gt = re.search(r'>\s*(\d+)', action)
            low = int(lt.group(1)) if lt else None
            high = int(gt.group(1)) if gt else None
            fn = make_conditional_sum_range_filter(seed_sum_min=smin, seed_sum_max=smax, low=low, high=high)
            fns.append({'name': name, 'fn': fn, 'descr': logic})
            continue
        # Mirror Count = 0
        if 'mirror count = 0' in lower_name:
            fns.append({'name': name, 'factory': 'mirror_zero', 'descr': logic})
            continue
        # Position filters, e.g., "Position 3 cannot be 3 or 9"
        m_pos = re.search(r'position\s*(\d+)\s*cannot be\s*([0-9](?:\s*or\s*[0-9])*)', lower_name)
        if m_pos:
            pos = int(m_pos.group(1))
            digs = re.findall(r'\d', m_pos.group(2))
            fns.append({'name': name, 'factory': ('position_forbid', pos, digs), 'descr': logic})
            continue
        # Add more patterns: e.g., high-end digit limit, consecutive, repeating, etc.
        st.warning(f"No function defined for manual filter: '{name}'")
    return fns

# ==============================
# Load manual filters from external file or upload
# ==============================
def load_manual_filters_from_file(uploaded_file=None, filepath_txt="manual_filters_degrouped.txt"):
    content = None
    if uploaded_file is not None:
        try:
            content = uploaded_file.read().decode('utf-8', errors='ignore')
            st.write("Loaded raw manual filters from uploaded file")
        except Exception as e:
            st.warning(f"Failed reading uploaded file: {e}")
    else:
        paths_to_try = [filepath_txt, os.path.join(os.getcwd(), filepath_txt), f"/mnt/data/{filepath_txt}"]
        for path in paths_to_try:
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    st.write(f"Loaded raw manual filters from {path}")
                    break
                except Exception as e:
                    st.warning(f"Failed reading manual filters from {path}: {e}")
    if content is None:
        st.info("No manual filters loaded. Upload TXT or place manual_filters_degrouped.txt in app directory.")
        return []
    raw_lines = content.splitlines()
    st.text_area("Raw manual filter lines", value="\n".join(raw_lines[:50]), height=200)
    parsed = parse_manual_filters_txt(content)
    st.write(f"Parsed {len(parsed)} manual filter blocks")
    st.text_area("Preview manual filter names", value="\n".join(p['name'] for p in parsed[:20]), height=200)
    return parsed

# ==============================
# Apply manual filter: wrapper to call function factory
# ==============================
def apply_manual_filter_fn(fn_entry, combo, seed, hot_digits, cold_digits, due_digits):
    combo_str = combo
    seed_str = str(seed)
    seed_sum = calculate_seed_sum(seed_str)
    mirror_set = mirror_digits(seed)
    if 'fn' in fn_entry:
        fn = fn_entry['fn']
    else:
        fac = fn_entry.get('factory')
        if fac == 'mirror_zero':
            fn = make_mirror_zero_filter(mirror_set)
        elif isinstance(fac, tuple) and fac[0] == 'position_forbid':
            pos, digs = fac[1], fac[2]
            fn = make_position_forbid_filter(pos, digs)
        else:
            return False
    keep, removed = fn([combo_str], seed_sum=seed_sum)
    return len(removed) == 1

# ==============================
# Trap V3 Ranking Integration
# ==============================
def rank_with_trap_v3(combos, seed):
    try:
        import dc5_trapv3_model as trap_model
        return trap_model.rank_combinations(combos, str(seed))
    except ImportError:
        st.warning("Trap V3 model not available. Ensure dc5_trapv3_model is in path.")
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
uploaded = st.sidebar.file_uploader("Upload manual filters file (TXT degrouped)", type=['txt'])

# Load manual filters
parsed_filters = []
if uploaded is not None or os.path.exists("manual_filters_degrouped.txt") or os.path.exists(f"/mnt/data/manual_filters_degrouped.txt"):
    parsed_filters = load_manual_filters_from_file(uploaded)
filter_entries = build_filter_functions(parsed_filters)

# Generate base pool after core filters
if seed:
    combos_initial = generate_combinations(seed, method)
    filtered_initial = [c for c in combos_initial if not core_filters(c, seed, method=method)]
    st.session_state['original_pool'] = filtered_initial.copy()

# Compute static elimination counts
def compute_static_counts():
    counts = []
    pool = st.session_state.get('original_pool', [])
    if seed and filter_entries:
        for fe in filter_entries:
            cnt = len([c for c in pool if apply_manual_filter_fn(fe, c, seed, hot_digits, cold_digits, due_digits)])
            counts.append((fe, cnt))
        counts.sort(key=lambda x: x[1])
    return counts

ranking_sorted = compute_static_counts()
st.markdown("## Manual Filters (Least → Most Aggressive)")
if not filter_entries:
    st.info("No manual filters loaded. Upload a degrouped TXT or place manual_filters_degrouped.txt in app directory.")
# Apply selected filters
session_pool = st.session_state.get('original_pool', []).copy() if seed else []
for idx, (fe, static_count) in enumerate(ranking_sorted):
    col1, col2 = st.columns([0.85, 0.15])
    label = fe['name']
    checkbox_label = f"{label} — would eliminate {static_count} combos"
    checked = col1.checkbox(checkbox_label, key=f"filter_cb_{idx}")
    if col2.button("?", key=f"help_{idx}"):
        elim = len([c for c in session_pool if apply_manual_filter_fn(fe, c, seed, hot_digits, cold_digits, due_digits)])
        st.info(f"Filter: {fe['name']}\nSession elimination: {elim} combos")
    if checked and seed:
        session_pool = [c for c in session_pool if not apply_manual_filter_fn(fe, c, seed, hot_digits, cold_digits, due_digits)]

if seed:
    st.session_state['session_pool'] = session_pool
    st.markdown(f"**Final Remaining combos after selected manual filters:** {len(session_pool)}")
    with st.expander("Show all remaining combinations"):
        if session_pool:
            for combo in session_pool:
                st.write(combo)
        else:
            st.write("No combinations remaining.")

# Trap V3 Ranking
if enable_trap and seed:
    st.markdown("## Trap V3 Ranking")
    ranked_list = rank_with_trap_v3(st.session_state.get('session_pool', []), seed)
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
