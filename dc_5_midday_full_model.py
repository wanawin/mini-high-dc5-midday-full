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

def digit_spread(combo):
    digits = sorted(int(d) for d in combo)
    return digits[-1] - digits[0]

# Mirror digit logic: mirror of d is 9 - d

def mirror_digits(combo):
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
        # generate unique 2-digit pairs from seed
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
    # TODO: implement percentile logic externally; stub passes all
    return True

def core_filters(combo, seed):
    # Return True if should be eliminated by core
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

def load_manual_filters(filepath="manual_filters.txt"):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r") as f:
                lines = []
                for line in f:
                    text = line.strip()
                    if not text:
                        continue
                    # Remove leading numbering if present (e.g., "1. ...")
                    if text and text[0].isdigit():
                        parts = text.split('.', 1)
                        if len(parts) == 2:
                            text = parts[1].strip()
                    # Replace any em-dash or en-dash with hyphen
                    text = text.replace('—', '-').replace('–', '-')
                    lines.append(text)
            return lines
        except Exception as e:
            st.error(f"Error loading manual filters from {filepath}: {e}")
            return []
    else:
        # Inline fallback list: names must match apply_manual_filter startswith logic
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
            # Add remaining filters here, one per line, without numbering prefix
        ]

manual_filters_list = load_manual_filters()

# ==============================
# Helper: apply_manual_filter
# ==============================
def apply_manual_filter(filter_text, combo, seed, hot_digits, cold_digits, due_digits):
    combo_str = combo
    seed_str = str(seed)
    # Cold Digit Trap
    if filter_text.startswith("Cold Digit Trap"):
        # Requires at least 1 digit from cold_digits
        for d in cold_digits:
            if d and d in combo_str:
                return False
        return True
    # Mirror Count = 0
    if filter_text.startswith("Mirror Count"):
        mirrors = mirror_digits(seed_str)
        return not any(d in mirrors for d in combo_str)
    # Repeating Digit Filter
    if filter_text.startswith("Repeating Digit Filter"):
        s = sum(int(d) for d in combo_str)
        if any(combo_str.count(d) >= 3 for d in set(combo_str)) and s < 25:
            return True
        return False
    # Sum > 40
    if filter_text.startswith("Sum > 40"):
        return sum(int(d) for d in combo_str) > 40
    # Digit Spread < 4
    if filter_text.startswith("Digit Spread < 4"):
        return digit_spread(combo_str) < 4
    # High-End Digit Limit
    if filter_text.startswith("High-End Digit Limit"):
        return sum(1 for d in combo_str if int(d) >= 8) >= 2
    # All Low Digits (0-3)
    if filter_text.startswith("All Low Digits"):
        return all(0 <= int(d) <= 3 for d in combo_str)
    # Consecutive Digits >= 4
    if filter_text.startswith("Consecutive Digits"):
        return has_consecutive_run(combo_str, run_length=4)
    # Double-Doubles Only
    if filter_text.startswith("Double-Doubles Only"):
        counts = [combo_str.count(d) for d in set(combo_str)]
        return not (len(counts) == 3 and sorted(counts) == [1,2,2])
    # Quint Filter
    if filter_text.startswith("Quint Filter"):
        return any(combo_str.count(d) == 5 for d in set(combo_str))
    # Quad Filter
    if filter_text.startswith("Quad Filter"):
        return any(combo_str.count(d) == 4 for d in set(combo_str))
    # Triple Filter
    if filter_text.startswith("Triple Filter") and "Repeating" not in filter_text:
        return any(combo_str.count(d) == 3 for d in set(combo_str))
    # Mild Double-Double Filter
    if filter_text.startswith("Mild Double-Double Filter"):
        counts = [combo_str.count(d) for d in set(combo_str)]
        return not (len(counts) == 4 and 2 in counts and counts.count(2) == 1)
    # No 2-Digit Internal Mirror Pairs
    if filter_text.startswith("No 2-Digit Internal Mirror Pairs"):
        for d in combo_str:
            if str(9-int(d)) in combo_str:
                return True
        return False
    # Prime Digit Filter
    if filter_text.startswith("Prime Digit Filter"):
        primes = {'2','3','5','7'}
        return sum(1 for d in combo_str if d in primes) >= 2
    # Sum Category Transition - placeholder
    if filter_text.startswith("Sum Category Transition"):
        return False
    # Mirror Sum = Combo Sum
    if filter_text.startswith("Mirror Sum = Combo Sum"):
        mirror_sum = sum(int(d) for d in mirror_digits(seed_str))
        return sum(int(d) for d in combo_str) == mirror_sum
    # Combo Contains Last Digit of Mirror Sum
    if filter_text.startswith("Combo Contains Last Digit of Mirror Sum"):
        mirror_sum = sum(int(d) for d in mirror_digits(seed_str))
        last = str(mirror_sum)[-1]
        return last in combo_str
    # Seed Contains X -> Require Y
    if filter_text.startswith("Seed Contains") and "->" in filter_text:
        parts = filter_text.split("->")
        if len(parts) == 2:
            cond, req = parts
            digit = cond.split()[-1].strip()
            required = [r.strip() for r in req.replace("Require","").split(',')]
            if digit in seed_str:
                return not any(r in combo_str for r in required)
        return False
    # V-Trac filters: placeholder
    if filter_text.startswith("V-Trac"):
        return False
    # Position-based filters
    if filter_text.startswith("Position 1 Cannot Be"):
        bans = [b.strip() for b in filter_text.split("Be")[1].split("or")]
        return combo_str[0] in bans
    if filter_text.startswith("Position 3 Cannot Be"):
        bans = [b.strip() for b in filter_text.split("Be")[1].split("or")]
        return combo_str[2] in bans
    if filter_text.startswith("Position 4 Cannot Be"):
        bans = [b.strip() for b in filter_text.split("Be")[1].split("or")]
        return combo_str[3] in bans
    if filter_text.startswith("Position 5 Cannot Be"):
        bans = [b.strip() for b in filter_text.split("Be")[1].split("or")]
        return combo_str[4] in bans
    # Eliminate if Digit X Repeats
    if filter_text.startswith("Eliminate if Digit"):
        digit = filter_text.split()[3]
        return combo_str.count(digit) > 1
    # Seed Contains pair and sum filters
    if filter_text.startswith("Seed Contains 00"):
        s = sum(int(d) for d in combo_str)
        return ("00" in seed_str) and (s < 11 or s > 33)
    if filter_text.startswith("Seed Contains 02"):
        s = sum(int(d) for d in combo_str)
        return ("02" in seed_str) and (s < 7 or s > 26)
    if filter_text.startswith("Seed Contains 03"):
        s = sum(int(d) for d in combo_str)
        return ("03" in seed_str) and (s < 13 or s > 35)
    if filter_text.startswith("Seed Contains 04"):
        s = sum(int(d) for d in combo_str)
        return ("04" in seed_str) and (s < 10 or s > 29)
    if filter_text.startswith("Seed Contains 05"):
        s = sum(int(d) for d in combo_str)
        return ("05" in seed_str) and (s < 10 or s > 30)
    if filter_text.startswith("Seed Contains 06"):
        s = sum(int(d) for d in combo_str)
        return ("06" in seed_str) and (s < 8 or s > 29)
    if filter_text.startswith("Seed Contains 07"):
        s = sum(int(d) for d in combo_str)
        return ("07" in seed_str) and (s < 8 or s > 28)
    # Shared Digits vs Sum Thresholds - placeholder
    if filter_text.startswith("Shared Digits vs Sum Thresholds"):
        return False
    # Default: do not eliminate
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
if seed:
    combos_initial = generate_combinations(seed, method)
    filtered_initial = [c for c in combos_initial if not core_filters(c, seed)]
    docs_remaining = filtered_initial.copy()
else:
    docs_remaining = []

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
# - Ensure manual_filters_list contains all filter names exactly matching apply_manual_filter cases.
# - For manual_filters.txt, remove numbering and ensure plain hyphens, no special dashes.
# - Extend apply_manual_filter with logic for any missing filters.
# - For V-Trac and Sum Category transitions, implement external logic or mapping as needed.
# - Now clicking a checkbox applies actual filter logic.
