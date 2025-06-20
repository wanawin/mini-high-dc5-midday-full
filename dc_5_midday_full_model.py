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
    "Cold Digit Trap — Requires at least 1 digit from the 4 coldest digits.",
    # ... other filter descriptions ...
    "Shared Digits vs Sum Thresholds — Grouped Set (Filters #1–4, 36–40, 71–79, 106–175)"
]

# ==============================
# Helper: apply_manual_filter
# ==============================

def apply_manual_filter(filter_text, combo, seed, hot_digits, cold_digits, due_digits):
    # Example implementations (expand as needed)
    if filter_text.startswith("Sum > 40"):
        return sum(int(d) for d in combo) > 40
    if filter_text.startswith("Digit Spread < 4"):
        digits = [int(d) for d in combo]
        return max(digits) - min(digits) < 4
    if filter_text.startswith("Consecutive Digits ≥ 4"):
        return has_consecutive_run(combo, 4)
    # default
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

# Generate base pool after core filters
combos_initial = generate_combinations(seed, method) if seed else []
filtered_initial = [c for c in combos_initial if not core_filters(c, seed)] if seed else []

# Compute elimination counts per filter (for display only)
ranking = []
for filt in manual_filters_list:
    eliminated = [c for c in filtered_initial if apply_manual_filter(filt, c, seed, hot_digits, cold_digits, due_digits)]
    ranking.append((filt, len(eliminated)))
ranking_sorted = sorted(ranking, key=lambda x: x[1])

st.markdown("## Manual Filters (Least → Most Aggressive)")

docs_remaining = filtered_initial.copy()
for filt, count in ranking_sorted:
    col1, col2 = st.columns([0.9, 0.1])
    checked = col1.checkbox(f"{filt} — would eliminate {count} combos", key=filt)
    if col2.button("?", key=f"help_{filt}"):
        st.info(f"Filter: {filt}\nEliminates {count} combinations in this session")
    if checked:
        to_remove = [c for c in docs_remaining if apply_manual_filter(filt, c, seed, hot_digits, cold_digits, due_digits)]
        docs_remaining = [c for c in docs_remaining if c not in to_remove]
        col1.write(f"Remaining combos after '{filt}': {len(docs_remaining)}")

st.markdown(f"**Final Remaining combos after selected manual filters:** {len(docs_remaining)}")

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
