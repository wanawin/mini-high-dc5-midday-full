import streamlit as st
from dc5_midday_full_model import (
    generate_combinations,
    core_filters,
    manual_filters_list
)

# ==============================
# Streamlit App Helper: apply_manual_filter stub
# ==============================
def apply_manual_filter(filter_text, combo, seed, hot_digits, cold_digits, due_digits):
    """
    Stub for mapping each manual filter description to its logic.
    Extend this function to call the appropriate filter functions based on filter_text.
    """
    # Example placeholder logic:
    # if filter_text.startswith("Digit Spread < 4"):
    #     return max(combo) - min(combo) < 4
    return False

# ==============================
# DC-5 Midday Blind Predictor (Streamlit App)
# ==============================
st.title("DC-5 Midday Blind Predictor")

# --- Sidebar Inputs ---
seed = st.sidebar.text_input("5-digit seed:")
hot_digits = st.sidebar.text_input("Hot digits (comma-separated):").replace(' ', '').split(',')
cold_digits = st.sidebar.text_input("Cold digits (comma-separated):").replace(' ', '').split(',')
due_digits = st.sidebar.text_input("Due digits (comma-separated):").replace(' ', '').split(',')
method = st.sidebar.selectbox("Generation Method:", ["1-digit", "2-digit pair"])

# --- Manual Filter Toggles ---
selected_manual = st.sidebar.multiselect(
    "Select Manual Filters to Apply", 
    manual_filters_list
)

st.sidebar.markdown("---")
if st.sidebar.button("Run Prediction"):
    # Generate combinations (deduplication built into generate_combinations)
    combos = generate_combinations(seed, method)
    st.write(f"Total generated combos: {len(combos)}")

    # Apply core (automatic) filters
    filtered = [c for c in combos if not core_filters(c, seed, None)]
    st.write(f"After core filters: {len(filtered)} combos remain")

    # Display intermediate results
    remaining = filtered
    for filt in selected_manual:
        eliminated = [c for c in remaining if apply_manual_filter(filt, c, seed, hot_digits, cold_digits, due_digits)]
        st.write(f"**{filt}** eliminated {len(eliminated)} combos")
        if st.checkbox(f"Show eliminated combos for: {filt}"):
            st.write(eliminated)
        remaining = [c for c in remaining if c not in eliminated]
        st.write(f"Remaining combos: {len(remaining)}")

    st.write("### Final Predictive Pool")
    st.dataframe(remaining)
