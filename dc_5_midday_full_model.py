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
                combos.add(''.join(sorted(d + ''.join(p))))
    else:
        pairs = set(''.join(sorted((seed[i], seed[j])))
                    for i in range(len(seed)) for j in range(i+1, len(seed)))
        for pair in pairs:
            for p in product(all_digits, repeat=3):
                combos.add(''.join(sorted(pair + ''.join(p))))
    return sorted(combos)

# ==============================
# Core filters: percentile stub and seed intersection
# ==============================

def primary_percentile_pass(combo):
    # TODO: implement percentile logic
    return True

def core_filters(combo, seed):
    if not primary_percentile_pass(combo):
        return True
    seed_combos = set(generate_combinations(seed))
    if combo not in seed_combos:
        return True
    return False

# ==============================
# Manual filter definitions (static, ranked externally)
# ==============================

manual_filters_list = [
    "Digit Spread < 4",
    "Sum > 40",
    "3+ Digits > 5",
    "All Digits 0–5",
    "≥4 Digits in Same V-Trac Group",
    "All 5 V-Trac Groups Present",
    "Only 2 V-Trac Groups Used",
    "Double-Doubles Only",
    "No digit 0 in Position 3",
    "No repeat of 0, 2, or 3",
    "Eliminate Triples (3 of same digit)",
    "Eliminate Quads (4 of same digit)",
    "Eliminate Quints (5 of same digit)",
    "Eliminate if 4 or more digits ≥8",
    "Consecutive Digit Count ≥ 4",
    "Very Low → Mid",
    "Mid → Very Low",
    "Low → Mid",
    "High → Very Low",
    "High → Low",
    "High → Mid",
    "Sum < 10",
    "Sum ending in 0",
    "Sum ending in 5",
    "Sum = 36",
    "Sum = 34",
    "Sum = 37",
    "Contains three repeating digits",
    "Triple Double Structure (A×3, B×2)",
    "Repeats digit 4",
    "Repeats digit 7",
    "2+ digits are prime (2,3,5,7)",
    "All digits are low (0–3)",
    "All digits are high (7–9)",
    "Mirror sum contains last digit of combo",
    "Mirror sum in 6–13",
    "Mirror sum = 14",
    "Mirror sum in 15–16",
    "If seed has 1 → require 2, 3, or 4",
    "If seed has 2 → require 5 or 4",
    "If seed contains 0 → require 1, 2, or 3",
    "00 seed pair → Eliminate if sum <11 or >33",
    "02 seed pair → Eliminate if sum <7 or >26",
    "03 seed pair → Eliminate if sum <13 or >35",
    "04 seed pair → Eliminate if sum <10 or >29",
    "05 seed pair → Eliminate if sum <10 or >30",
    "06 seed pair → Eliminate if sum <8 or >29",
    "07 seed pair → Eliminate if sum <8 or >28",
    "Seed Sum starts with 2 & Result Sum starts with 1",
    "Seed Sum starts with 2 & Result Sum starts with 3",
    "Seed Sum starts with 2 & Result Sum starts with 4",
    "≥1 shared & sum <10",
    "≥1 shared & sum <11",
    "≥1 shared & sum <12",
    "≥2 shared & sum <10",
    "Shared Digits vs Sum Thresholds — Grouped Set (Filters #1–4, 36–40, 71–79, 106–175)",
]

# ==============================
# Helper: apply_manual_filter
# ==============================

def apply_manual_filter(filter_text, combo, seed, hot_digits, cold_digits, due_digits):
    """
    Return True if the combo should be eliminated by the given filter_text.
    """
    # Precompute metrics
    counts = [combo.count(d) for d in set(combo)]
    digit_list = [int(d) for d in combo]
    digit_sum = sum(digit_list)

    # Sum filters
    if filter_text.startswith("Sum > 40"):
        return digit_sum > 40
    if filter_text.startswith("Sum < 10"):
        return digit_sum < 10
    if filter_text.startswith("Sum ending in 0"):
        return digit_sum % 10 == 0
    if filter_text.startswith("Sum ending in 5"):
        return digit_sum % 10 == 5
    if filter_text.startswith("Sum = 34"):
        return digit_sum == 34
    if filter_text.startswith("Sum = 36"):
        return digit_sum == 36
    if filter_text.startswith("Sum = 37"):
        return digit_sum == 37

    # Spread filter
    if filter_text.startswith("Digit Spread < 4"):
        return max(digit_list) - min(digit_list) < 4

    # High-end digit limit
    if filter_text.startswith("Eliminate if 4 or more digits ≥8"):
        return sum(1 for d in digit_list if d >= 8) >= 4

    # Triples/Quads/Quints
    if filter_text.startswith("Eliminate Triples"):
        return any(c == 3 for c in counts)
    if filter_text.startswith("Eliminate Quads"):
        return any(c == 4 for c in counts)
    if filter_text.startswith("Eliminate Quints"):
        return any(c == 5 for c in counts)

    # Double-Doubles Only
    if filter_text.startswith("Double-Doubles Only"):
        # two digits appear twice and one appears once
        return sorted(counts) == [1,2,2]

    # No digit 0 in Position 3
    if filter_text.startswith("No digit 0 in Position 3"):
        return combo[2] == '0'

    # No repeat of 0, 2, or 3
    if filter_text.startswith("No repeat of 0, 2, or 3"):
        return any(combo.count(d) > 1 for d in ['0','2','3'])

    # 3+ Digits > 5
    if filter_text.startswith("3+ Digits > 5"):
        return sum(1 for d in digit_list if d > 5) >= 3

    # All Digits 0–5
    if filter_text.startswith("All Digits 0–5"):
        return all(d <= 5 for d in digit_list)

    # Consecutive Digit Count ≥ 4
    if filter_text.startswith("Consecutive Digit Count"):
        return has_consecutive_run(combo, 4)

    # Default: no elimination
    return False
# ==============================
# Streamlit App

st.title("DC-5 Midday Blind Predictor")

# Sidebar inputs
seed = st.sidebar.text_input("5-digit seed:")
hot_digits = st.sidebar.text_input("Hot digits (comma-separated):").replace(' ', '').split(',')
cold_digits = st.sidebar.text_input("Cold digits (comma-separated):").replace(' ', '').split(',')
due_digits = st.sidebar.text_input("Due digits (comma-separated):").replace(' ', '').split(',')
method = st.sidebar.selectbox("Generation Method:", ["1-digit", "2-digit pair"])

# Generate base pool after core filters
target = []
combos_initial = generate_combinations(seed, method) if seed else []
filtered_initial = [c for c in combos_initial if not core_filters(c, seed)] if seed else []

# Prepare remaining pool
docs_remaining = filtered_initial.copy()

# Compute static elimination counts for ranking
ranking = [(filt, len([c for c in filtered_initial if apply_manual_filter(filt, c, seed, hot_digits, cold_digits, due_digits)]))
           for filt in manual_filters_list]
ranking_sorted = sorted(ranking, key=lambda x: x[1])

st.markdown("## Manual Filters (Least → Most Aggressive)")

# Display filters with dynamic counts
for filt, static_count in ranking_sorted:
    col1, col2 = st.columns([0.9, 0.1])
    checkbox_label = f"{filt} — would eliminate {static_count} combos"
    checked = col1.checkbox(checkbox_label, key=filt)

    # Help popup shows current elimination count
    if col2.button("?", key=f"help_{filt}"):
        current_to_remove = [c for c in docs_remaining if apply_manual_filter(filt, c, seed, hot_digits, cold_digits, due_digits)]
        st.info(f"Filter: {filt}
Eliminates {len(current_to_remove)} combinations in this session")

    # When checked, remove and show dynamic eliminated count and remaining
    if checked:
        to_remove = [c for c in docs_remaining if apply_manual_filter(filt, c, seed, hot_digits, cold_digits, due_digits)]
        eliminated_count = len(to_remove)
        docs_remaining = [c for c in docs_remaining if c not in to_remove]
        col1.write(f"Eliminated {eliminated_count} combos; Remaining combos: {len(docs_remaining)}")

st.markdown(f"**Final Remaining combos after selected manual filters:** {len(docs_remaining)}")

# Trap V3 Ranking (optional)
if st.sidebar.checkbox("Enable Trap V3 Ranking"):
    digits = [int(d) for d in seed]
    trap_combos = set()
    if method == '1-digit':
        for d in digits:
            for p in product(range(10), repeat=4):
                trap_combos.add(''.join(map(str, sorted((d, *p)))))
    else:
        for a, b in combinations(digits, 2):
            for p in product(range(10), repeat=3):
                trap_combos.add(''.join(map(str, sorted((a, b, *p)))))
    trap_sorted = sorted(c for c in trap_combos if c in docs_remaining)
    st.write("## Trap V3 Ranked Combos")
    st.dataframe(trap_sorted)

# Prediction button
if st.sidebar.button("Run Prediction"):
    combos = combos_initial
    st.write(f"Total generated combos: {len(combos)}")
    filtered = [c for c in combos if not core_filters(c, seed)]
    st.write(f"After core filters: {len(filtered)} combos remain")
    remaining = filtered.copy()
    for filt in manual_filters_list:
        eliminated = [c for c in remaining if apply_manual_filter(filt, c, seed, hot_digits, cold_digits, due_digits)]
        st.write(f"**{filt}** eliminated {len(eliminated)} combos")
        remaining = [c for c in remaining if c not in eliminated]
        st.write(f"Remaining combos: {len(remaining)}")
    st.write("### Final Predictive Pool")
    st.dataframe(remaining)

 (optional)
if st.sidebar.checkbox("Enable Trap V3 Ranking"):
    digits = [int(d) for d in seed]
    trap_combos = set()
    if method == '1-digit':
        for d in digits:
            for p in product(range(10), repeat=4):
                trap_combos.add(''.join(map(str, sorted((d, *p)))))
    else:
        for a, b in combinations(digits, 2):
            for p in product(range(10), repeat=3):
                trap_combos.add(''.join(map(str, sorted((a, b, *p)))))
    trap_sorted = sorted(c for c in trap_combos if c in docs_remaining)
    st.write("## Trap V3 Ranked Combos")
    st.dataframe(trap_sorted)
