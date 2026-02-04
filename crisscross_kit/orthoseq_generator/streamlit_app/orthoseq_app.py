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
    )

    # hello world

    # 1. Page Config
    st.set_page_config(page_title="Orthoseq Generator UI", layout="wide")
    st.title("Orthoseq Generator UI")

    # 2. Session State and Logging
    init_session_state()
    setup_logger(st.session_state.log_queue)
    drain_log_queue()

    if st.session_state.search_running or st.session_state.pilot_running or st.session_state.refine_running:
        st_autorefresh(interval=500, key="global_poll")

    st.subheader("Logs")
    st.text_area(
        "Algorithm log",
        value="\n".join(st.session_state.log_buffer[-500:]),
        height=150
    )

    # 3. Sidebar: Global Settings
    st.sidebar.header("Global Settings")
    seq_length = st.sidebar.number_input(
        "Sequence Length", min_value=1, max_value=100, value=20, disabled=st.session_state.busy
    )
    fivep_ext = st.sidebar.text_input("5' Extension", value="", disabled=st.session_state.busy)
    threep_ext = st.sidebar.text_input("3' Extension", value="", disabled=st.session_state.busy)

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
    apply_to = st.sidebar.selectbox("Apply Unwanted to", ["core", "full"], index=0, disabled=st.session_state.busy)
    random_seed = st.sidebar.number_input("Random Seed", value=42, disabled=st.session_state.busy)

    st.sidebar.subheader("NUPACK Parameters")
    material = st.sidebar.selectbox("Material", ["dna", "rna"], index=0, disabled=st.session_state.busy)
    celsius = st.sidebar.number_input("Temperature (C)", value=37.0, format="%.1f", disabled=st.session_state.busy)
    sodium = st.sidebar.number_input("Sodium (M)", value=0.05, format="%.4f", disabled=st.session_state.busy)
    magnesium = st.sidebar.number_input("Magnesium (M)", value=0.025, format="%.4f", disabled=st.session_state.busy)

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
        'sync_func': sync_nupack_params
    }

    # 4. Navigation
    nav = st.radio(
        "Workflow Step",
        ["1. Exploratory Analysis", "2. Range Refinement", "3. Orthogonal Search"],
        key="active_step",
        horizontal=True,
        disabled=st.session_state.busy
    )

    if nav == "1. Exploratory Analysis":
        render_exploratory_tab(get_registry, nupack_params)
    elif nav == "2. Range Refinement":
        render_refinement_tab(get_registry, nupack_params)
    else:
        render_search_tab(get_registry, nupack_params)


