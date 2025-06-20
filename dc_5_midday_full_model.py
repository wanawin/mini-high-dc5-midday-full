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
    # Returns set of mirror digits (9 - digit)
    return {str(9 - int(d)) for d in combo}

# ==============================
# Generate combinations function (deduplicated)
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
        # Build all 2-digit pairs from seed digits
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
    # INLINE COMMENT: Replace stub with actual percentile logic if available.
    return True

def core_filters(combo, seed, method="2-digit pair"):
    # Return True if combo should be eliminated by core filters
    if not primary_percentile_pass(combo):
        return True
    # Intersection: keep only combos generated from seed in selected method
    seed_combos = set(generate_combinations(seed, method=method))
    if combo not in seed_combos:
        return True
    return False

# ==============================
# Manual filter definitions (dynamic load from CSV or file)
# ==============================
def load_manual_filters(filepath_txt="manual_filters.txt", filepath_csv="DC5_Midday_Filter_List__With_Descriptions_.csv"):
    filters = []
    # Try CSV first: expect a column named 'Filter Name' or similar
    if os.path.exists(filepath_csv):
        try:
            df = pd.read_csv(filepath_csv)
            col_candidates = [c for c in df.columns if 'filter' in c.lower() or 'name' in c.lower()]
            if col_candidates:
                for text in df[col_candidates[0]].astype(str).tolist():
                    text = text.strip()
                    if not text:
                        continue
                    text = text.replace('—', '-').replace('–', '-')
                    # Remove leading numbering
                    if text and text[0].isdigit():
                        parts = text.split('.', 1)
                        if len(parts) == 2 and parts[0].isdigit():
                            text = parts[1].strip()
                    filters.append(text)
                return filters
        except Exception as e:
            st.warning(f"Failed loading CSV manual filters: {e}")
    # Next try txt file
    if os.path.exists(filepath_txt):
        try:
            with open(filepath_txt, "r") as f:
                for line in f:
                    text = line.strip()
                    if not text:
                        continue
                    if text and text[0].isdigit():
                        parts = text.split('.', 1)
                        if len(parts) == 2 and parts[0].isdigit():
                            text = parts[1].strip()
                    text = text.replace('—', '-').replace('–', '-')
                    filters.append(text)
            return filters
        except Exception as e:
            st.warning(f"Error loading manual filters from txt: {e}")
    # Fallback: if neither file found, user must inline define all 115 filters here
    # For example:
    fallback = [
        # Individually ranked 42 filters
        "Cold Digit Trap - Requires at least 1 digit from the 4 coldest digits",
        "Mirror Count = 0 - Eliminate combos that do not contain any mirror digit from the seed",
        # ... add all 42 individually ranked filters ...
        # Grouped set 73 filters can be appended here
        # e.g., "Shared Digits vs Sum Thresholds - Grouped Set ...",
        # ... continue for all ...
    ]
    return fallback

manual_filters_list = load_manual_filters()

# ==============================
# Helper: implement each filter's logic
# ==============================
def apply_manual_filter(filter_text, combo, seed, hot_digits, cold_digits, due_digits):
    combo_str = ''.join(combo)
    seed_str = str(seed)
    total = sum(int(d) for d in combo_str)
    # Cold Digit Trap: requires at least one cold digit in combo; eliminate combos without any
    if filter_text.lower().startswith("cold digit trap"):
        for d in cold_digits:
            if d and d in combo_str:
                return False
        return True
    # Mirror Count = 0
    if filter_text.lower().startswith("mirror count = 0"):
        mirror_set = mirror_digits(seed_str)
        for d in combo_str:
            if d in mirror_set:
                return False
        return True
    # Sum > threshold
    if 'sum >' in filter_text.lower():
        try:
            import re
            m = re.search(r'sum >\s*(\d+)', filter_text.lower())
            if m:
                thresh = int(m.group(1))
                return total <= thresh
        except:
            return False
    # Digit Spread <
    if 'digit spread <' in filter_text.lower():
        try:
            import re
            m = re.search(r'digit spread <\s*(\d+)', filter_text.lower())
            if m:
                thresh = int(m.group(1))
                return digit_spread(combo_str) >= thresh
        except:
            return False
    # High-End Digit Limit or digits >=8
    if '>= 8' in filter_text or 'high-end digit limit' in filter_text.lower():
        count = sum(1 for d in combo_str if int(d) >= 8)
        return count < 2
    # All Low Digits 0-3
    if 'all low digits' in filter_text.lower() or '(0' in filter_text:
        return any(int(d) > 3 for d in combo_str)
    # Consecutive Digits >=
    if 'consecutive' in filter_text.lower():
        import re
        m = re.search(r'>=\s*(\d+)', filter_text)
        if m:
            run_len = int(m.group(1))
            return not has_consecutive_run(combo_str, run_length=run_len)
    # Double-Doubles Only
    if 'double-doubles only' in filter_text.lower():
        uniq = set(combo_str)
        if len(uniq) == 3:
            counts = [combo_str.count(d) for d in uniq]
            if sorted(counts) == [1,2,2]:
                return False
        return True
    # Quint, Quad, Triple
    if filter_text.lower().startswith("quint filter") or 'same digit repeated' in filter_text.lower():
        return len(set(combo_str)) != 1
    if filter_text.lower().startswith("quad filter") or 'digit appears 4 times' in filter_text.lower():
        return not any(combo_str.count(d) == 4 for d in set(combo_str))
    if filter_text.lower().startswith("triple filter") or 'digit appears 3 times' in filter_text.lower():
        return not any(combo_str.count(d) == 3 for d in set(combo_str))
    # No 2-Digit Internal Mirror Pairs
    if 'no 2-digit internal mirror' in filter_text.lower():
        for d in combo_str:
            if str(9-int(d)) in combo_str:
                return True
        return False
    # Prime Digit Filter
    if 'prime digit' in filter_text.lower():
        primes = {'2','3','5','7'}
        count = sum(1 for d in combo_str if d in primes)
        return count >= 2
    # Seed-based sum range filters e.g., "Seed Contains 00 and Sum <11 or >33"
    if filter_text.lower().startswith('seed contains') and 'sum' in filter_text.lower():
        import re
        # find digits pattern
        m_pair = re.search(r'seed contains ([0-9]{2})', filter_text.lower())
        if m_pair:
            pair = m_pair.group(1)
            if seed_str.count(pair[0]) >= pair.count(pair[0]) and pair[0]==pair[1]:
                # parse <a or >b
                ranges = re.findall(r'<\s*(\d+)|>\s*(\d+)', filter_text)
                for lt, gt in ranges:
                    if lt and total < int(lt): return True
                    if gt and total > int(gt): return True
        # other seed-pair patterns: implement similarly as needed
    # Position filters e.g., "Position 1 Cannot Be 4 or 7"
    if filter_text.lower().startswith('position'):
        import re
        m = re.match(r"position (\d+) cannot be (.*)", filter_text.lower())
        if m:
            pos = int(m.group(1)) - 1
            digits = [d.strip() for d in m.group(2).split('or')]
            if 0 <= pos < len(combo_str) and combo_str[pos] in digits:
                return True
            return False
    # Other filters: implement according to patterns
    # Default: do not eliminate
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
            # display in columns or paginated if large
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
