import streamlit as st
from itertools import product

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

# Generate combinations function (deduplicated)
def generate_combinations(seed, method="2-digit pair"):
    all_digits = '0123456789'
    combos = set()
    if method == "1-digit":
        for d in seed:
            for p in product(all_digits, repeat=4):
                combos.add(''.join(sorted(d + ''.join(p))))
    else:
        pairs = set(''.join(sorted((seed[i], seed[j]))) for i in range(len(seed)) for j in range(i+1, len(seed)))
        for pair in pairs:
            for p in product(all_digits, repeat=3):
                combos.add(''.join(sorted(pair + ''.join(p))))
    return sorted(combos)

# Automatic core filters: primary percentile stub and seed intersection
def primary_percentile_pass(combo):
    # TODO: implement percentile logic
    return True

def core_filters(combo, seed, previous_draw=None):
    if not primary_percentile_pass(combo):
        return True
    seed_combos = set(generate_combinations(seed))
    if combo not in seed_combos:
        return True
    return False

# Manual filter definitions
manual_filters_list = [
    "Digit Sum Range — Keeps only combinations where the digit sum is between 10 and 40",
    "Structure Filter (Singles + Doubles) — Eliminates Triples, Quads, Quints",
    "Follower Digit Trap — Requires at least 2 follower digits",
    "Cold Digit Trap — Requires at least one cold digit",
    "Repeating Digit Filter — Removes Singles with ≥3 shared digits and sum < 25",
    "Mirror Digit Trap — Requires at least 1 mirror digit",
    "Even/Odd Pattern Change — Must differ from previous draw’s pattern",
    "Trailing Digit Match Filter — Eliminates if last digit matches previous draw",
    "Lead Digit Match Filter — Eliminates if first digit matches previous draw",
    "Mirror Digit Count Filter — Eliminates if 3+ mirror digits",
    "All Same V-Trac Group — Eliminates if all digits same group",
    "Mirror Sum Filter — Eliminates if digit sum equals mirror sum",
    "4+ Digits ≥ 8 — Eliminates if 4+ digits ≥8",
    "Consecutive Digit Count ≥4 — Eliminates if 4+ consecutive digits",
    # Shared digits vs sum thresholds can be added here...
]

# ==============================
# Helper: apply_manual_filter
# ==============================
def apply_manual_filter(filter_text, combo, seed, hot_digits, cold_digits, due_digits):
    if filter_text.startswith("Digit Sum Range"):
        return not (10 <= sum(int(d) for d in combo) <= 40)
    if filter_text.startswith("4+ Digits ≥ 8"):
        return sum(1 for d in combo if int(d) >= 8) >= 4
    if filter_text.startswith("Consecutive Digit Count"):
        return has_consecutive_run(combo, 4)
    # Add other manual filter logic here mapping filter_text to functions
    return False

# ==============================
# Streamlit App
# ==============================
st.title("DC-5 Midday Blind Predictor")

# Sidebar inputs
seed = st.sidebar.text_input("5-digit seed:")
hot_digits = st.sidebar.text_input("Hot digits (comma-separated):").replace(' ', '').split(',')
cold_digits = st.sidebar.text_input("Cold digits (comma-separated):").replace(' ', '').split(',')
due_digits = st.sidebar.text_input("Due digits (comma-separated):").replace(' ', '').split(',')
method = st.sidebar.selectbox("Generation Method:", ["1-digit", "2-digit pair"])
selected_manual = st.sidebar.multiselect("Select Manual Filters to Apply", manual_filters_list)

if st.sidebar.button("Run Prediction"):
    combos = generate_combinations(seed, method)
    st.write(f"Total generated combos: {len(combos)}")
    # Core filters
    filtered = [c for c in combos if not core_filters(c, seed)]
    st.write(f"After core filters: {len(filtered)} combos remain")
    # Manual filters
    remaining = filtered.copy()
    for filt in selected_manual:
        eliminated = [c for c in remaining if apply_manual_filter(filt, c, seed, hot_digits, cold_digits, due_digits)]
        st.write(f"**{filt}** eliminated {len(eliminated)} combos")
        if st.checkbox(f"Show eliminated combos for: {filt}"):
            st.write(eliminated)
        remaining = [c for c in remaining if c not in eliminated]
        st.write(f"Remaining combos: {len(remaining)}")
    st.write("### Final Predictive Pool")
    st.dataframe(remaining)
