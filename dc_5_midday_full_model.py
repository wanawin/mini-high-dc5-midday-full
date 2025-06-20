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
        # Fallback static list: inline full filter list
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
            "Sum Category Transition Filter - Very Low to Mid",
            "Sum Category Transition Filter - Mid to Very Low",
            "Sum Category Transition Filter - Low to Mid",
            "Mirror Sum = Combo Sum - Eliminates combos whose digit sum matches seed mirror sum",
            "Combo Contains Last Digit of Mirror Sum",
            "Seed Contains 0 -> Winner must contain 1, 2, or 3",
            "Seed Contains 1 -> Winner must contain 2, 3, or 4",
            "Seed Contains 2 -> Winner must contain 4 or 5",
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
            # Continue listing all remaining filter names here...
        ]

manual_filters_list = load_manual_filters()

# ==============================
# Helper: apply_manual_filter
# ==============================

def apply_manual_filter(filter_text, combo, seed, hot_digits, cold_digits, due_digits):
    # INLINE COMMENT: Implement logic for each filter_text exactly as named.
    # Return True to eliminate combo, False to keep.

    # Example implementations for common filters:
    if "Eliminate Triples" in filter_text or "Triple Filter" in filter_text:
        for d in set(combo):
            if combo.count(d) >= 3:
                return True
        return False
    if "Eliminate Quads" in filter_text or "Quad Filter" in filter_text:
        for d in set(combo):
            if combo.count(d) >= 4:
                return True
        return False
    if "Eliminate Quints" in filter_text or "Quint Filter" in filter_text:
        return any(combo.count(d) == 5 for d in set(combo))
    if "Eliminate if 4 or more digits >=8" in filter_text or "High-End Digit Limit" in filter_text:
        count = sum(1 for d in combo if int(d) >= 8)
        return count >= 4
    # Add more filter logic below following names
    # e.g., Cold Digit Trap
    if "Cold Digit Trap" in filter_text:
        # Requires at least 1 digit from cold_digits
        for d in combo:
            if d in cold_digits:
                return False
        return True
    # Mirror Count = 0
    if "Mirror Count = 0" in filter_text:
        seed_str = str(seed)
        mirror_set = {str(9-int(d)) for d in seed_str}
        # Eliminate combos that do not contain any mirror digit
        for d in combo:
            if d in mirror_set:
                return False
        return True
    # Sum > 40
    if "Sum > 40" in filter_text:
        total = sum(int(d) for d in combo)
        return total > 40
    # Digit Spread < 4
    if "Digit Spread < 4" in filter_text:
        return digit_spread(combo) < 4
    # All Low Digits (0-3)
    if "All Low Digits" in filter_text:
        return all(int(d) <= 3 for d in combo)
    # Consecutive Digits >= 4
    if "Consecutive Digits >= 4" in filter_text:
        return has_consecutive_run(combo, run_length=4)
    # Double-Doubles Only
    if "Double-Doubles Only" in filter_text:
        unique = set(combo)
        if len(unique) == 3:
            counts = [combo.count(d) for d in unique]
            return sorted(counts) == [1,2,2]
        return False
    # Prime Digit Filter
    if "Prime Digit Filter" in filter_text:
        primes = {'2','3','5','7'}
        count = sum(1 for d in combo if d in primes)
        return count >= 2
    # Seed Contains 00 and Sum <11 or >33
    if "Seed Contains 00" in filter_text:
        seed_str = str(seed)
        if seed_str.count('0') >= 2:
            total = sum(int(d) for d in combo)
            return total < 11 or total > 33
        return False
    # Seed Contains 05 and Sum <10 or >30
    if "Seed Contains 05" in filter_text:
        seed_str = str(seed)
        if '0' in seed_str and '5' in seed_str:
            total = sum(int(d) for d in combo)
            return total < 10 or total > 30
        return False
    # Seed Contains 06 and Sum <8 or >29
    if "Seed Contains 06" in filter_text:
        seed_str = str(seed)
        if '0' in seed_str and '6' in seed_str:
            total = sum(int(d) for d in combo)
            return total < 8 or total > 29
        return False
    # Seed Contains 07 and Sum <8 or >28
    if "Seed Contains 07" in filter_text:
        seed_str = str(seed)
        if '0' in seed_str and '7' in seed_str:
            total = sum(int(d) for d in combo)
            return total < 8 or total > 28
        return False
    # Position restrictions
    if "Position 1 Cannot Be" in filter_text:
        parts = filter_text.split('Cannot Be')[-1].strip().split('or')
        bad = {p.strip() for p in parts}
        return combo[0] in bad
    if "Position 3 Cannot Be" in filter_text:
        parts = filter_text.split('Cannot Be')[-1].strip().split('or')
        bad = {p.strip() for p in parts}
        return combo[2] in bad
    if "Position 4 Cannot Be" in filter_text:
        parts = filter_text.split('Cannot Be')[-1].strip().split('or')
        bad = {p.strip() for p in parts}
        return combo[3] in bad
    if "Position 5 Cannot Be" in filter_text:
        parts = filter_text.split('Cannot Be')[-1].strip().split('or')
        bad = {p.strip() for p in parts}
        return combo[4] in bad
    # V-Trac and other complex filters to be implemented similarly
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
