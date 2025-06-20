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
    # ... existing filter list ...
]

# ==============================
# Helper: apply_manual_filter
# ==============================

def apply_manual_filter(filter_text, combo, seed, hot_digits, cold_digits, due_digits):
    # ... existing implementation ...
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
        st.info(f"Filter: {filt}\nEliminates {len(current_to_remove)} combinations in this session")

    # When checked, remove and show dynamic eliminated count and remaining
    if checked:
        to_remove = [c for c in docs_remaining if apply_manual_filter(filt, c, seed, hot_digits, cold_digits, due_digits)]
        eliminated_count = len(to_remove)
        docs_remaining = [c for c in docs_remaining if c not in to_remove]
        col1.write(f"Eliminated {eliminated_count} combos; Remaining combos: {len(docs_remaining)}")

st.markdown(f"**Final Remaining combos after selected manual filters:** {len(docs_remaining)}")

# ... rest of the app ...
