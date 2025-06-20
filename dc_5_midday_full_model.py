import streamlit as st
from itertools import product, combinations
import os

# ==============================
# Inline DC-5 Midday Model Functions
# ==============================
# These helper functions support filter logic and seed processing.

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
# Generates all sorted combos based on seed and method.

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
# Manual filter definitions (static, ranked externally)
# ==============================

def load_manual_filters(filepath="manual_filters.txt"):
    # Load filters from file or fallback to static list
    if os.path.exists(filepath):
        try:
            filters = []
            with open(filepath, "r") as f:
                for line in f:
                    text = line.strip()
                    if not text:
                        continue
                    # Remove leading numbering if present
                    if text and text[0].isdigit():
                        parts = text.split('.', 1)
                        if len(parts) == 2 and parts[0].isdigit():
                            text = parts[1].strip()
                    # Normalize dashes: replace en/em with hyphen
                    text = text.replace('—', '-').replace('–', '-')
                    filters.append(text)
            return filters
        except Exception as e:
            st.error(f"Error loading manual filters from {filepath}: {e}")
            return []
    else:
        # Fallback static list: populate this inline or ensure manual_filters.txt exists
        # INLINE COMMENT: Replace the below examples with your full filter list if file missing
        return [
            "Eliminate Triples (any digit appears 3 times)",
            "Eliminate Quads (any digit appears 4 times)",
            "Eliminate Quints (same digit repeated)",
            "Eliminate if 4 or more digits >=8",
            # ... add all filter texts here or via manual_filters.txt
        ]

manual_filters_list = load_manual_filters()

# ==============================
# Helper: apply_manual_filter
# ==============================

def apply_manual_filter(filter_text, combo, seed, hot_digits, cold_digits, due_digits):
    # INLINE COMMENT: Implement logic for each filter_text exactly as named.
    # Return True to eliminate combo, False to keep.

    # Example implementations for common filters:
    if "Eliminate Triples" in filter_text:
        # Any digit appears 3 or more times
        for d in set(combo):
            if combo.count(d) >= 3:
                return True
        return False
    if "Eliminate Quads" in filter_text:
        for d in set(combo):
            if combo.count(d) >= 4:
                return True
        return False
    if "Eliminate Quints" in filter_text:
        return any(combo.count(d) == 5 for d in set(combo))
    if "Eliminate if 4 or more digits >=8" in filter_text:
        count = sum(1 for d in combo if int(d) >= 8)
        return count >= 4
    # INLINE COMMENT: Continue adding cases for each filter in manual_filters_list
    # For example:
    # if "Cold Digit Trap" in filter_text:
    #     # Requires at least 1 digit from cold_digits
    #     for d in combo:
    #         if d in cold_digits:
    #             return False
    #     return True

    # Default: keep combo
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
    # Apply core filters
    filtered_initial = [c for c in combos_initial if not core_filters(c, seed, method=method)]
    current_pool = filtered_initial.copy()

# Compute static elimination counts for ranking
if seed:
    ranking = []
    for filt in manual_filters_list:
        count_elim = len([c for c in current_pool if apply_manual_filter(filt, c, seed, hot_digits, cold_digits, due_digits)])
        ranking.append((filt, count_elim))
    # Sort filters by static elimination count (least to most aggressive)
    ranking_sorted = sorted(ranking, key=lambda x: x[1])
else:
    ranking_sorted = [(filt, 0) for filt in manual_filters_list]

st.markdown("## Manual Filters (Least → Most Aggressive)")

# Use a copy for session filtering
session_pool = current_pool.copy() if seed else []

for idx, (filt, static_count) in enumerate(ranking_sorted):
    col1, col2 = st.columns([0.85, 0.15])
    key_cb = f"filter_cb_{idx}"
    key_help = f"help_{idx}"
    checkbox_label = f"{filt} — would eliminate {static_count} combos"
    checked = col1.checkbox(checkbox_label, key=key_cb)

    # Help button: show session-specific elimination count
    if col2.button("?", key=key_help):
        if seed:
            current_to_remove = [c for c in session_pool if apply_manual_filter(filt, c, seed, hot_digits, cold_digits, due_digits)]
            st.info(f"Filter: {filt}\nEliminates {len(current_to_remove)} combinations in this session")
    # If checked, remove combos and show inline count
    if checked and seed:
        to_remove = [c for c in session_pool if apply_manual_filter(filt, c, seed, hot_digits, cold_digits, due_digits)]
        eliminated_count = len(to_remove)
        session_pool = [c for c in session_pool if c not in to_remove]
        col1.write(f"Eliminated {eliminated_count} combos; Remaining combos: {len(session_pool)}")

st.markdown(f"**Final Remaining combos after selected manual filters:** {len(session_pool)}")

# Show all remaining combinations in an expander (single instance)
if seed:
    with st.expander("Show all remaining combinations"):
        if session_pool:
            for combo in session_pool:
                st.write(combo)
        else:
            st.write("No combinations remaining.")

# Trap V3 Ranking display
if enable_trap and seed:
    st.markdown("## Trap V3 Ranking")
    ranked_list = rank_with_trap_v3(session_pool, seed)
    if ranked_list:
        st.write("Top combinations by Trap V3:")
        # Show top 20
        for combo in ranked_list[:20]:
            st.write(combo)
        if len(ranked_list) > 20:
            with st.expander("Show all ranked combinations"):
                for combo in ranked_list:
                    st.write(combo)
    else:
        st.write("No combinations to rank or ranking failed.")

# Notes:
# - Ensure manual_filters_list is populated with the full filter texts either via manual_filters.txt or inline list.
# - Fill in apply_manual_filter logic for each named filter exactly.
# - INLINE COMMENTS present above to guide where to add logic.
# - Only one expander for remaining combos and one for ranked combos.
# - Dashes in filter names should be hyphens ('-'), not special en/em dashes.
# - If manual_filters_list is empty, verify manual_filters.txt path or inline default list.
