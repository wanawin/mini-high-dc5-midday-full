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

# Manual filter definitions (static, ranked externally)
# TODO: Replace the list below with your finalized manual filters ordered least to most aggressive.
manual_filters_list = [
    "Cold Digit Trap — Requires at least 1 digit from the 4 coldest digits.",
    "Mirror Count = 0 — Eliminate combos that do not contain any mirror digit from the seed.",
    "Repeating Digit Filter (3+ Shared & Sum < 25) — For Singles only.",
    "Sum > 40 — Eliminates combos where digit sum is over 40.",
    "Digit Spread < 4 — Eliminates combos with low spread between digits.",
    "High-End Digit Limit — Eliminates if 2 or more digits ≥ 8.",
    "All Low Digits (0–3) — Eliminates if all 5 digits are from 0 to 3.",
    "Consecutive Digits ≥ 4 — Eliminates clusters of consecutive digits.",
    "Double-Doubles Only — Eliminates combos with exactly 3 unique digits, two of which appear twice.",
    "Quint Filter — All 5 digits identical.",
    "Quad Filter — 4 digits identical.",
    "Triple Filter — 3 digits identical.",
    "Mild Double-Double Filter — Exactly 4 digits: one twice, two once.",
    "No 2-Digit Internal Mirror Pairs — Eliminates combos with digit and its mirror.",
    "Prime Digit Filter — Eliminates combos with ≥2 prime digits (2,3,5,7).",
    "Sum Category Transition Filter — Very Low to Mid.",
    "Sum Category Transition Filter — Mid to Very Low.",
    "Sum Category Transition Filter — Low to Mid.",
    "Mirror Sum = Combo Sum — Eliminates combos whose digit sum matches seed mirror sum.",
    "Combo Contains Last Digit of Mirror Sum — Manual filter.",
    "Seed Contains 0 → Winner must contain 1, 2, or 3.",
    "Seed Contains 1 → Winner must contain 2, 3, or 4.",
    "Seed Contains 2 → Winner must contain 4 or 5.",
    "V-Trac: All Digits Same Group — Eliminates if all digits share the same V-Trac group.",
    "V-Trac: Only 2 Groups Present — Eliminates if only 2 V-Trac groups used.",
    "V-Trac: All 5 Groups Present — Eliminates if all 5 V-Trac groups used.",
    "V-Trac: All Seed V-Tracs Present — Eliminates if all V-Trac groups from seed are in combo.",
    "V-Trac: None of Seed V-Tracs Present — Eliminates if no seed V-Tracs in combo.",
    "Position 1 Cannot Be 4 or 7 — Manual trap filter.",
    "Position 3 Cannot Be 3 or 9 — Manual trap filter.",
    "Position 4 Cannot Be 4 — Manual trap filter.",
    "Position 5 Cannot Be 4 — Manual trap filter.",
    "Eliminate if Digit 4 Repeats.",
    "Eliminate if Digit 7 Repeats.",
    "Seed Contains 00 and Sum <11 or >33.",
    "Seed Contains 02 and Sum <7 or >26.",
    "Seed Contains 03 and Sum <13 or >35.",
    "Seed Contains 04 and Sum <10 or >29.",
    "Seed Contains 05 and Sum <10 or >30.",
    "Seed Contains 06 and Sum <8 or >29.",
    "Seed Contains 07 and Sum <8 or >28.",
    "Shared Digits vs Sum Thresholds — Grouped Set (Filters #1–4, 36–40, 71–79, 106–175)"
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

# === Manual Filters (Always Visible with Help) ===
# Generate base pool after core filters for current seed
combos_initial = generate_combinations(seed, method) if seed else []
filtered_initial = [c for c in combos_initial if not core_filters(c, seed)] if seed else []
# Compute elimination counts per filter
ranking = []
for filt in manual_filters_list:
    eliminated = [c for c in filtered_initial if apply_manual_filter(filt, c, seed, hot_digits, cold_digits, due_digits)]
    ranking.append((filt, len(eliminated)))
# Sort from least to most aggressive
ranking_sorted = sorted(ranking, key=lambda x: x[1])

st.markdown("## Manual Filters (Least → Most Aggressive)")
selected_manual = []
# Display each filter with checkbox and help button
for filt, count in ranking_sorted:
    col1, col2 = st.columns([0.9, 0.1])
    checked = col1.checkbox(f"{filt} — eliminates {count} combos", key=filt)
    if col2.button("?", key=f"help_{filt}"):
        st.info(f"Filter: {filt}
Eliminates {count} combinations in this session")
    if checked:
        selected_manual.append(filt)

# --- Run Prediction ---
if st.sidebar.button("Run Prediction"):
if st.sidebar.button("Run Prediction"):
    combos = combos_initial
    st.write(f"Total generated combos: {len(combos)}")
    # Core filters
    filtered = [c for c in combos if not core_filters(c, seed)]
    st.write(f"After core filters: {len(filtered)} combos remain")
    # Manual filters
    remaining = filtered.copy()
    for filt in selected_manual:
        eliminated = [c for c in remaining if apply_manual_filter(filt, c, seed, hot_digits, cold_digits, due_digits)]
        st.write(f"**{filt}** eliminated {len(eliminated)} combos")
        if st.sidebar.checkbox(f"Show eliminated combos for: {filt}"):
            st.write(eliminated)
        remaining = [c for c in remaining if c not in eliminated]
        st.write(f"Remaining combos: {len(remaining)}")
    st.write("### Final Predictive Pool")
    st.dataframe(remaining)("Run Prediction"):
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
