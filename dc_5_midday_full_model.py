import streamlit as st
from itertools import product, combinations
import os

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
# ==============================
# Load manual filters from an external file (one filter name per line) or define inline list.
# Place a file named 'manual_filters.txt' alongside this script with each filter name on its own line
# in the desired order. If file not present, use inline default list (populate with full filters).

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
        # Fallback: inline list (populate manually with full filters in desired order)
        return [
            "Cold Digit Trap - Requires at least 1 digit from the 4 coldest digits",
            "Mirror Count = 0 - Eliminate combos that do not contain any mirror digit from the seed",
            "Repeating Digit Filter (3+ Shared & Sum < 25) - For Singles only",
            "Sum > 40 - Eliminates combos where digit sum is over 40",
            "Digit Spread < 4 - Eliminates combos with low spread between digits",
            "High-End Digit Limit - Eliminates if 2 or more digits >= 8",
            "All Low Digits (0-3) - Eliminates if all 5 digits are from 0 to 3",
            "Consecutive Digits >= 4 - Eliminates clusters of consecutive digits",
            "Double-Doubles Only - Eliminates combos with exactly 3 unique digits, two of which appear twice",
            "Quint Filter - All 5 digits identical",
            "Quad Filter - 4 digits identical",
            "Triple Filter - 3 digits identical",
            "Mild Double-Double Filter - Exactly 4 digits: one twice, two once",
            "No 2-Digit Internal Mirror Pairs - Eliminates combos with digit and its mirror",
            "Prime Digit Filter - Eliminates combos with >=2 prime digits (2,3,5,7)",
            "Sum Category Transition - Very Low to Mid",
            "Sum Category Transition - Mid to Very Low",
            "Sum Category Transition - Low to Mid",
            "Mirror Sum = Combo Sum - Eliminates combos whose digit sum matches seed mirror sum",
            "Combo Contains Last Digit of Mirror Sum - Eliminates if mirror sum contains last digit of combo",
            "Seed Contains 0 -> Require 1,2, or 3",
            "Seed Contains 1 -> Require 2,3, or 4",
            "Seed Contains 2 -> Require 4 or 5",
            "V-Trac: All Digits Same Group - Eliminates if all digits share the same V-Trac group",
            "V-Trac: Only 2 Groups Present - Eliminates if only 2 V-Trac groups used",
            "V-Trac: All 5 Groups Present - Eliminates if all 5 V-Trac groups used",
            "V-Trac: All Seed V-Tracs Present - Eliminates if all V-Trac groups from seed are in combo",
            "V-Trac: None of Seed V-Tracs Present - Eliminates if no seed V-Tracs in combo",
            "Position 1 Cannot Be 4 or 7",
            "Position 3 Cannot Be 3 or 9",
            "Position 4 Cannot Be 4",
            "Position 5 Cannot Be 4",
            "Eliminate if Digit 4 Repeats",
            "Eliminate if Digit 7 Repeats",
            "Seed Contains 00 and Sum <11 or >33",
            "Seed Contains 02 and Sum <7 or >26",
            "Seed Contains 03 and Sum <13 or >35",
            "Seed Contains 04 and Sum <10 or >29",
            "Seed Contains 05 and Sum <10 or >30",
            "Seed Contains 06 and Sum <8 or >29",
            "Seed Contains 07 and Sum <8 or >28",
            "Shared Digits vs Sum Thresholds - Grouped Set",
            # Add other filters #71-#175 here appropriately
        ]

manual_filters_list = load_manual_filters()

# ==============================
# Helper: apply_manual_filter
# ==============================
def apply_manual_filter(filter_text, combo, seed, hot_digits, cold_digits, due_digits):
    """Return True if combo should be eliminated by this manual filter."""
    # Implement logic matching filter_text as needed, using ASCII hyphens
    if filter_text.startswith("Eliminate Triples"):
        return any(combo.count(d) >= 3 for d in set(combo))
    if filter_text.startswith("Eliminate Quads"):
        return any(combo.count(d) >= 4 for d in set(combo))
    if filter_text.startswith("Eliminate Quints") or filter_text.startswith("Quint Filter"):
        return any(combo.count(d) == 5 for d in set(combo))
    if filter_text.startswith("Eliminate if 4 or more digits >=8") or filter_text.startswith("High-End Digit Limit"):
        return sum(1 for d in combo if int(d) >= 8) >= 2 if "High-End Digit Limit" in filter_text else sum(1 for d in combo if int(d) >= 8) >= 4
    # Additional implementations to be added...
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
    key_cb = f"filter_cb_{idx}_{filt}"
    key_help = f"help_{idx}_{filt}"
    checkbox_label = f"{filt} — would eliminate {static_count} combos"
    checked = col1.checkbox(checkbox_label, key=key_cb)

    if col2.button("?", key=key_help):
        if seed:
            current_to_remove = [c for c in current_pool if apply_manual_filter(filt, c, seed, hot_digits, cold_digits, due_digits)]
            st.info(f"Filter: {filt}\nEliminates {len(current_to_remove)} combinations in this session")
    if checked and seed:
        to_remove = [c for c in current_pool if apply_manual_filter(filt, c, seed, hot_digits, cold_digits, due_digits)]
        eliminated_count = len(to_remove)
        current_pool = [c for c in current_pool if c not in to_remove]
        col1.write(f"Eliminated {eliminated_count} combos; Remaining combos: {len(current_pool)}")

st.markdown(f"**Final Remaining combos after selected manual filters:** {len(current_pool)}")

# Note:
# - To list all manual filters, create 'manual_filters.txt' with one name per line in desired order.
# - Extend apply_manual_filter with logic for each filter_text.
# - Ensure keys are unique for checkboxes/buttons to persist state.
# - For performance, consider caching generate_combinations if needed.
