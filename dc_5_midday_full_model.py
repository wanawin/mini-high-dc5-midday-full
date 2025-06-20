import streamlit as st
from itertools import product

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
    manual_filters_list,
    format_func=lambda x: x
)

st.sidebar.markdown("---")
if st.sidebar.button("Run Prediction"):
    # Generate combos
    combos = generate_combinations(seed, method)
    st.write(f"Total generated combos: {len(combos)}")

    # Apply core (automatic) filters
    filtered = [c for c in combos if not core_filters(c, seed, None)]
    st.write(f"After core filters: {len(filtered)} combos remain")

    # Display remaining combos
    st.dataframe(filtered)

    # Sequentially apply manual filters
    remaining = filtered.copy()
    for filt in selected_manual:
        # apply_manual_filter should map filter text to its function
        eliminated = [c for c in remaining if apply_manual_filter(filt, c, seed, hot_digits, cold_digits, due_digits)]
        st.write(f"**{filt}** eliminated {len(eliminated)} combos")
        if st.checkbox(f"Show eliminated combos for: {filt}"):
            st.write(eliminated)
        remaining = [c for c in remaining if c not in eliminated]
        st.write(f"Remaining combos: {len(remaining)}")

    st.write("### Final Predictive Pool")
    st.dataframe(remaining)

# Note: implement apply_manual_filter mapping each filter description to its logic.
# Existing filter functions (shared_digits_count, has_consecutive_run, etc.) can be used inside apply_manual_filter.
