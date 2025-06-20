import streamlit as st
from itertools import product, combinations

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

# ==============================
# Generate combinations function (deduplicated)
# ==============================

def generate_combinations(seed, method="2-digit pair"):
    all_digits = '0123456789'
    combos = set()
    if method == "1-digit":
        for d in seed:
            for p in product(all_digits, repeat=4):
                combo = ''.join(sorted(d + ''.join(p)))
                combos.add(combo)
    else:
        pairs = set(''.join(sorted((seed[i], seed[j])))
                    for i in range(len(seed)) for j in range(i+1, len(seed)))
        for pair in pairs:
            for p in product(all_digits, repeat=3):
                combo = ''.join(sorted(pair + ''.join(p)))
                combos.add(combo)
    return sorted(combos)

# ==============================
# Core filters: percentile stub and seed intersection
# ==============================

def primary_percentile_pass(combo):
    # TODO: implement percentile logic externally; stub passes all
    return True

def core_filters(combo, seed):
    if not primary_percentile_pass(combo):
        return True
    # Intersection: keep only combos generated from seed
    # Note: generating full set repeatedly can be expensive; consider caching
    seed_combos = set(generate_combinations(seed, method="2-digit pair"))
    if combo not in seed_combos:
        return True
    return False

# ==============================
# Manual filter definitions (static, ranked externally)
# Load manual filters from an external file (one filter name per line) or define inline list.
# Place a file named 'manual_filters.txt' alongside this script with each filter name on its own line in the desired order.
import os

def load_manual_filters(filepath="manual_filters.txt"):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r") as f:
                lines = [line.strip() for line in f if line.strip()]
            return lines
        except Exception as e:
            st.error(f"Error loading manual filters from {filepath}: {e}")
            return []
    else:
        # Fallback: inline list (populate manually)
        return [
            "Eliminate Triples (any digit appears 3 times)",
            "Eliminate Quads (any digit appears 4 times)",
            "Eliminate Quints (same digit repeated)",
            "Eliminate if 4 or more digits ≥8",
            # Add additional filters here if not using external file
        ]

# Populate manual_filters_list with either loaded or inline
manual_filters_list = load_manual_filters()
# ===============================
# Populate this list with all manual filter names in desired least→most aggressive order.
manual_filters_list = [
    # Example structural filters; extend with full list
    "Eliminate Triples (any digit appears 3 times)",
    "Eliminate Quads (any digit appears 4 times)",
    "Eliminate Quints (same digit repeated)",
    "Eliminate if 4 or more digits ≥8",  
    # Add all other filters here, in final ranked order
]

# ==============================
# Helper: apply_manual_filter
# ==============================
def apply_manual_filter(filter_text, combo, seed, hot_digits, cold_digits, due_digits):
    """Return True if combo should be eliminated by this manual filter."""
    if filter_text == "Eliminate Triples (any digit appears 3 times)":
        return any(combo.count(d) >= 3 for d in set(combo))
    if filter_text == "Eliminate Quads (any digit appears 4 times)":
        return any(combo.count(d) >= 4 for d in set(combo))
    if filter_text == "Eliminate Quints (same digit repeated)":
        return any(combo.count(d) == 5 for d in set(combo))
    if filter_text == "Eliminate if 4 or more digits ≥8":
        return sum(1 for d in combo if int(d) >= 8) >= 4
    # TODO: implement other filter cases by matching filter_text
    return False

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

# Generate base pool after core filters
docs_remaining = []
if seed:
    combos_initial = generate_combinations(seed, method)
    # Apply core filters
    filtered_initial = [c for c in combos_initial if not core_filters(c, seed)]
    docs_remaining = filtered_initial.copy()

# Compute static elimination counts for ranking
ranking = []
if seed:
    for filt in manual_filters_list:
        count_elim = len([c for c in docs_remaining if apply_manual_filter(filt, c, seed, hot_digits, cold_digits, due_digits)])
        ranking.append((filt, count_elim))
    # Sort by static elimination count
    ranking_sorted = sorted(ranking, key=lambda x: x[1])
else:
    ranking_sorted = [(filt, 0) for filt in manual_filters_list]

st.markdown("## Manual Filters (Least → Most Aggressive)")

# Apply manual filters in order; use local copy each render
if seed:
    current_pool = docs_remaining.copy()
else:
    current_pool = []

for idx, (filt, static_count) in enumerate(ranking_sorted):
    col1, col2 = st.columns([0.85, 0.15])
    # Use a safe key for each checkbox/button
    key_cb = f"filter_cb_{idx}_{filt}"
    key_help = f"help_{idx}_{filt}"
    checkbox_label = f"{filt} — would eliminate {static_count} combos"
    checked = col1.checkbox(checkbox_label, key=key_cb)

    # Help popup: count elimination if applied now
    if col2.button("?", key=key_help):
        if seed:
            current_to_remove = [c for c in current_pool if apply_manual_filter(filt, c, seed, hot_digits, cold_digits, due_digits)]
            st.info(f"Filter: {filt}\nEliminates {len(current_to_remove)} combinations in this session")
    # When checked, apply filter to current_pool
    if checked and seed:
        to_remove = [c for c in current_pool if apply_manual_filter(filt, c, seed, hot_digits, cold_digits, due_digits)]
        eliminated_count = len(to_remove)
        current_pool = [c for c in current_pool if c not in to_remove]
        col1.write(f"Eliminated {eliminated_count} combos; Remaining combos: {len(current_pool)}")

st.markdown(f"**Final Remaining combos after selected manual filters:** {len(current_pool)}")

# Note:
# - Populate manual_filters_list with all filter identifiers in your final ranked order.
# - Extend apply_manual_filter with logic for each filter_text.
# - Ensure keys are unique for checkboxes and buttons to persist state.
# - Avoid expensive repeated generation in core_filters by caching if needed.
