if __name__ == "__main__":
    import streamlit as st
    from orthoseq_generator import helper_functions as hf
    from orthoseq_generator import sequence_computations as sc
    from orthoseq_generator.streamlit_app.state_manager import init_session_state
    from streamlit_autorefresh import st_autorefresh
    from orthoseq_generator.streamlit_app.logging_utils import setup_logger, drain_log_queue
    from orthoseq_generator.streamlit_app.tabs import (
        render_exploratory_tab,
        render_refinement_tab,
        render_search_tab,
        render_selection_helper_tab,
    )

    # hello world

    # 1. Page Config
    st.set_page_config(page_title="Orthoseq Generator", layout="wide")
    st.title("Orthoseq")

    # 2. Session State and Logging
    init_session_state()
    setup_logger(st.session_state.log_queue)
    drain_log_queue()

    if st.session_state.search_running or st.session_state.pilot_running or st.session_state.refine_running:
        st_autorefresh(interval=500, key="global_poll")

    st.subheader("Logs")
    st.text_area(
        "Computations:",
        value="\n".join(st.session_state.log_buffer[-500:]),
        height=150
    )

    # 3. Sidebar: Global Settings
    st.sidebar.header("Global Settings")
    st.sidebar.subheader("Sequence Layout")
    st.sidebar.image(
        "crisscross_kit/orthoseq_generator/streamlit_app/graphics/on_target.png",
        width='content'
    )

    def _validate_dna_extension(label, value):
        cleaned = value.strip()
        if not cleaned:
            return True, ""
        invalid = sorted(set(cleaned.upper()) - set("ACGT"))
        if invalid:
            st.sidebar.error(
                f"{label} must contain only A, C, G, T (got: {', '.join(invalid)}). T is U for RNA"
            )
            return False, cleaned
        return True, cleaned.upper()

    seq_length = st.sidebar.number_input(
        "Sequence Length", min_value=2, max_value=100, value=10, disabled=st.session_state.busy
    )
    fivep_ext_input = st.sidebar.text_input("5' Extension", value="", disabled=st.session_state.busy)
    threep_ext_input = st.sidebar.text_input("3' Extension", value="", disabled=st.session_state.busy)
    valid_fivep, fivep_ext = _validate_dna_extension("5' Extension", fivep_ext_input)
    valid_threep, threep_ext = _validate_dna_extension("3' Extension", threep_ext_input)
    st.session_state.input_invalid = not (valid_fivep and valid_threep)

    custom_unwanted = st.sidebar.text_input(
        "Custom Unwanted Substrings (comma separated)", value="", disabled=st.session_state.busy
    )
    default_unwanted = ["AAAA", "CCCC", "GGGG", "TTTT", "AAAAA", "CCCCC", "GGGGG", "TTTTT"]

    unwanted = st.sidebar.multiselect(
        "Unwanted Substrings",
        default_unwanted + ([s.strip() for s in custom_unwanted.split(",") if s.strip()] if custom_unwanted else []),
        default=["AAAA", "CCCC", "GGGG", "TTTT"],
        disabled=st.session_state.busy
    )
    apply_to_label = st.sidebar.selectbox(
        "Apply Unwanted to",
        ["Core", "Full"],
        index=0,
        disabled=st.session_state.busy
    )
    apply_to = apply_to_label.lower()

    st.sidebar.subheader("Physical Quantities")
    material_label = st.sidebar.selectbox(
        "Material",
        ["DNA", "RNA"],
        index=0,
        disabled=st.session_state.busy
    )
    material = material_label.lower()
    celsius = st.sidebar.number_input("Temperature (C)", value=37.0, format="%.1f", disabled=st.session_state.busy)
    sodium = st.sidebar.number_input("Sodium (M)",min_value=0.05,max_value=1.1, value=0.05, format="%.4f", disabled=st.session_state.busy)
    magnesium = st.sidebar.number_input("Magnesium (M)", min_value=0.0, max_value=0.2, value=0.025, format="%.4f", disabled=st.session_state.busy)

    st.sidebar.subheader("Random Seed")
    random_seed = st.sidebar.number_input(" ", value=42, disabled=st.session_state.busy)

    # Registry Factory helper
    def get_registry():
        return sc.SequencePairRegistry(
            length=seq_length,
            fivep_ext=fivep_ext,
            threep_ext=threep_ext,
            unwanted_substrings=unwanted,
            apply_unwanted_to=apply_to,
            seed=random_seed
        )

    def sync_nupack_params():
        hf.set_nupack_params(
            material=material,
            celsius=celsius,
            sodium=sodium,
            magnesium=magnesium
        )

    nupack_params = {
        'random_seed': random_seed,
        'sync_func': sync_nupack_params,
        'seq_length': seq_length,
        'fivep_ext': fivep_ext,
        'threep_ext': threep_ext,
        'unwanted': unwanted,
        'apply_to': apply_to,
        'material': material,
        'celsius': celsius,
        'sodium': sodium,
        'magnesium': magnesium,
    }

    # 4. Navigation
    nav = st.radio(
        "Workflow Steps",
        ["1. Selection Helper", "2. Pilot Analysis", "3. Off-Target Limit", "4. Sequence Search"],
        key="active_step",
        horizontal=True,
        disabled=st.session_state.busy
    )

    if nav == "1. Selection Helper":
        render_selection_helper_tab(nupack_params)
    elif nav == "2. Pilot Analysis":
        render_exploratory_tab(get_registry, nupack_params)
    elif nav == "3. Off-Target Limit":
        render_refinement_tab(get_registry, nupack_params)
    else:
        render_search_tab(get_registry, nupack_params)
