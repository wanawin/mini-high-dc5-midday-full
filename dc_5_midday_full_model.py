import streamlit as st
from itertools import product, combinations
import os
import re

# ==============================
# BOOT CHECKPOINT
# ==============================
st.title("🤪 DC-5 Midday Filter App")
st.success("✅ App loaded: Boot successful.")

# ==============================
# Manual Filter Parsing
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

def build_filter_functions(parsed_filters):
    fns = []
    for pf in parsed_filters:
        raw_name = pf['name'].strip()
        logic = pf.get('logic','')
        action = pf.get('action','')

        name_norm = (raw_name
                     .replace('≥', '>=')
                     .replace('≤', '<=')
                     .replace('→', '->')
                     .replace('–', '-')
                     .replace('—', '-'))
        lower_name = name_norm.lower()

        m_hyphen = re.search(r'seed sum\s*(\d+)\s*-\s*(\d+)', lower_name)
        m_le     = re.search(r'seed sum\s*<=\s*(\d+)', lower_name)
        m_ge     = re.search(r'seed sum\s*>=\s*(\d+)', lower_name)
        m_eq     = re.search(r'seed sum\s*=\s*(\d+)', lower_name)

        if m_hyphen or m_le or m_ge or m_eq:
            seed_sum_min = seed_sum_max = None
            if m_hyphen:
                seed_sum_min = int(m_hyphen.group(1))
                seed_sum_max = int(m_hyphen.group(2))
            elif m_le:
                seed_sum_max = int(m_le.group(1))
            elif m_ge:
                seed_sum_min = int(m_ge.group(1))
            elif m_eq:
                seed_sum_min = seed_sum_max = int(m_eq.group(1))

            low = high = None
            m_between = re.search(r'between\s*(\d+)\s*(?:and|-)\s*(\d+)', action, flags=re.IGNORECASE)
            if m_between:
                low = int(m_between.group(1))
                high = int(m_between.group(2))
            else:
                m_le2 = re.search(r'sum\s*<=\s*(\d+)', action)
                m_lt2 = re.search(r'sum\s*<\s*(\d+)', action)
                m_ge2 = re.search(r'sum\s*>=\s*(\d+)', action)
                m_gt2 = re.search(r'sum\s*>\s*(\d+)', action)
                if m_le2:
                    high = int(m_le2.group(1))
                elif m_lt2:
                    high = int(m_lt2.group(1)) - 1
                if m_ge2:
                    low = int(m_ge2.group(1))
                elif m_gt2:
                    low = int(m_gt2.group(1)) + 1

            def make_conditional_sum_range_filter(seed_sum_min, seed_sum_max, low, high):
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

            fn = make_conditional_sum_range_filter(seed_sum_min, seed_sum_max, low, high)
            fns.append({'name': raw_name, 'fn': fn, 'descr': logic})
            continue

        if 'seed contains' in lower_name and 'winner must contain' in lower_name:
            m_seed_contains = re.search(r'seed contains\s*(\d+)', lower_name)
            m_winner_must = re.search(r'winner must contain\s*([\d,\s orand]+)', lower_name)
            if m_seed_contains and m_winner_must:
                seed_digit = m_seed_contains.group(1)
                reqs = re.findall(r'\d+', m_winner_must.group(1))
                reqs = set(reqs)
                def make_must_contain_filter(seed_digit, reqs):
                    def filter_fn(combo_list, seed=None, **kwargs):
                        if seed is not None and str(seed_digit) in str(seed):
                            keep, removed = [], []
                            for c in combo_list:
                                if any(d in c for d in reqs):
                                    keep.append(c)
                                else:
                                    removed.append(c)
                            return keep, removed
                        return combo_list, []
                    return filter_fn
                fn = make_must_contain_filter(seed_digit, reqs)
                fns.append({'name': raw_name, 'fn': fn, 'descr': logic})
                continue

        if 'all digits are low' in lower_name:
            def low_digits_filter(combo_list, **kwargs):
                keep, removed = [], []
                for combo in combo_list:
                    if all(int(d) <= 3 for d in combo):
                        removed.append(combo)
                    else:
                        keep.append(combo)
                return keep, removed
            fns.append({'name': raw_name, 'fn': low_digits_filter, 'descr': logic})
            continue

        if 'consecutive digit count' in lower_name:
            def has_consecutive_digits(combo):
                digits = sorted(int(d) for d in combo)
                streak = 1
                for i in range(1, len(digits)):
                    if digits[i] == digits[i - 1] + 1:
                        streak += 1
                        if streak >= 3:
                            return True
                    else:
                        streak = 1
                return False
            def consec_filter(combo_list, **kwargs):
                keep, removed = [], []
                for combo in combo_list:
                    if has_consecutive_digits(combo):
                        removed.append(combo)
                    else:
                        keep.append(combo)
                return keep, removed
            fns.append({'name': raw_name, 'fn': consec_filter, 'descr': logic})
            continue

    return fns
