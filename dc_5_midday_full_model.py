import streamlit as st
from itertools import product, combinations
import os
import re

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

def mirror_digits(seed):
    return {str(9 - int(d)) for d in str(seed) if d.isdigit()}

# ==============================
# Generate combinations function
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
        pairs = set(''.join(sorted((seed_str[i], seed_str[j])))
                    for i in range(len(seed_str)) for j in range(i+1, len(seed_str)))
        for pair in pairs:
            for p in product(all_digits, repeat=3):
                combo = ''.join(sorted(pair + ''.join(p)))
                combos.add(combo)
    return sorted(combos)

# ==============================
# Core filters: stub and seed intersection
# ==============================
def primary_percentile_pass(combo):
    return True

def core_filters(combo, seed, method="2-digit pair"):
    if not primary_percentile_pass(combo):
        return True
    seed_combos = set(generate_combinations(seed, method=method))
    if combo not in seed_combos:
        return True
    return False

# ==============================
# Parse manual filters TXT
# ==============================
def parse_manual_filters_txt(raw_text: str):
    entries = []
    blocks = [blk.strip() for blk in raw_text.strip().split("\n\n") if blk.strip()]
    for blk in blocks:
        lines = [ln.strip() for ln in blk.splitlines() if ln.strip()]
        if len(lines) >= 4:
            name = lines[0]
            type_line = lines[1]
            logic_line = lines[2]
            action_line = lines[3]
            typ = type_line.split(":", 1)[1].strip() if ":" in type_line else type_line
            logic = logic_line.split(":", 1)[1].strip() if ":" in logic_line else logic_line
            action = action_line.split(":", 1)[1].strip() if ":" in action_line else action_line
            entries.append({"name": name, "type": typ, "logic": logic, "action": action})
        else:
            st.warning(f"Skipped manual-filter block (not 4 lines): {blk[:50]}...")
    return entries

# ==============================
# Filter function factories
# ==============================
def make_conditional_sum_range_filter(seed_sum_min=None, seed_sum_max=None, low=None, high=None):
    def filter_fn(combo_list, seed_sum=None, **kwargs):
        if seed_sum is None:
            return combo_list, []
        if seed_sum_min is not None and seed_sum < seed_sum_min:
            return combo_list, []
        if seed_sum_max is not None and seed_sum > seed_sum_max:
            return combo_list, []
        keep, removed = [], []
        for combo in combo_list:
            s = sum(int(d) for d in combo)
            if (low is not None and s < low) or (high is not None and s > high):
                removed.append(combo)
            else:
                keep.append(combo)
        return keep, removed
    return filter_fn

def make_mirror_zero_filter(mirror_set):
    def filter_fn(combo_list, **kwargs):
        if not mirror_set:
            return combo_list, []
        keep, removed = [], []
        for combo in combo_list:
            if any(d in mirror_set for d in combo):
                keep.append(combo)
            else:
                removed.append(combo)
        return keep, removed
    return filter_fn

def make_position_forbid_filter(pos, forbid_digits):
    def filter_fn(combo_list, **kwargs):
        keep, removed = [], []
        for combo in combo_list:
            if combo[pos-1] in forbid_digits:
                removed.append(combo)
            else:
                keep.append(combo)
        return keep, removed
    return filter_fn

def make_seed_contains_requires_filter(seed_digit, required_digits):
    def filter_fn(combo_list, seed=None, **kwargs):
        if seed is None:
            return combo_list, []
        keep, removed = [], []
        for combo in combo_list:
            if str(seed_digit) in str(seed):
                if not any(d in combo for d in required_digits):
                    removed.append(combo)
                    continue
            keep.append(combo)
        return keep, removed
    return filter_fn

# ==============================
# Build filter functions from parsed entries
# ==============================
def build_filter_functions(parsed_filters):
    fns = []
    for pf in parsed_filters:
        name = pf['name']
        logic = pf['logic']
        action = pf['action']
        lower_name = name.lower()
        # Seed Sum filters
        m_seed = re.search(r'seed sum\s*[≤<=]?\s*(\d+)(?:[\-–](\d+))?', lower_name)
        if m_seed:
            if m_seed.group(2):
                smin = int(m_seed.group(1)); smax = int(m_seed.group(2))
            else:
                val = int(m_seed.group(1))
                if '≤' in name or '<=' in lower_name:
                    smin = None; smax = val
                else:
                    smin = val; smax = val
            lt = re.search(r'sum\s*<\s*(\d+)', action)
            gt = re.search(r'>\s*(\d+)', action)
            low = int(lt.group(1)) if lt else None
            high = int(gt.group(1)) if gt else None
            fn = make_conditional_sum_range_filter(seed_sum_min=smin, seed_sum_max=smax, low=low, high=high)
            fns.append({'name': name, 'fn': fn, 'descr': logic})
            continue
        # Digit dependency filter: seed contains X → winner must contain Y or Z
        m_dep = re.search(r'seed contains\s*(\d).*?winner must contain.*?(\d).*?(\d)', lower_name)
        if m_dep:
            seed_digit = m_dep.group(1)
            required_digits = [m_dep.group(2), m_dep.group(3)]
            fn = make_seed_contains_requires_filter(seed_digit, required_digits)
            fns.append({'name': name, 'fn': fn, 'descr': logic})
            continue
        # Mirror Count = 0
        if 'mirror count = 0' in lower_name:
            fns.append({'name': name, 'factory': 'mirror_zero', 'descr': logic})
            continue
        # Position filters
        m_pos = re.search(r'position\s*(\d+)\s*cannot be\s*([0-9](?:\s*or\s*[0-9])*)', lower_name)
        if m_pos:
            pos = int(m_pos.group(1))
            digs = re.findall(r'\d', m_pos.group(2))
            fns.append({'name': name, 'factory': ('position_forbid', pos, digs), 'descr': logic})
            continue
        st.warning(f"No function defined for manual filter: '{name}'")
    return fns
