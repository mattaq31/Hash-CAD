if __name__ == "__main__":
    import html
    import importlib.util
    import os
    import random
    import signal
    import threading
    import time
    from pathlib import Path
    import streamlit as st
    from orthoseq_generator import helper_functions as hf
    from orthoseq_generator import sequence_computations as sc
    from orthoseq_generator.streamlit_app.state_manager import init_session_state
    from streamlit_autorefresh import st_autorefresh
    from orthoseq_generator.streamlit_app.logging_utils import setup_logger, drain_log_queue
    from orthoseq_generator.streamlit_app.tabs import (
        render_exploratory_tab,
        render_load_results_tab,
        render_refinement_tab,
        render_search_tab,
        render_selection_helper_tab,
    )

    # hello world

    # 1. Page Config
    st.set_page_config(page_title="Orthoseq Generator", layout="wide")
    nupack_available = importlib.util.find_spec("nupack") is not None

    # 2. Session State and Logging
    init_session_state()
    setup_logger(st.session_state.log_queue)
    drain_log_queue()

    def _shutdown_streamlit_after_delay(delay_seconds=1.5):
        def _shutdown():
            time.sleep(delay_seconds)
            os.kill(os.getpid(), signal.SIGTERM)

        threading.Thread(target=_shutdown, daemon=True).start()

    if st.session_state.get("quit_app_requested", False):
        if not st.session_state.get("quit_app_shutdown_started", False):
            st.session_state.quit_app_shutdown_started = True
            _shutdown_streamlit_after_delay()
        st.title("OrthoSeq")
        st.warning("App closed. You can close this tab.")
        st.html(
            """
            <script>
            setTimeout(() => {
              window.close();
              setTimeout(() => {
                window.location.replace("about:blank");
              }, 250);
            }, 250);
            </script>
            """,
            width="stretch",
            unsafe_allow_javascript=True,
        )
        st.stop()

    title_col, quit_col = st.columns([9, 1])
    with title_col:
        st.title("OrthoSeq")
    with quit_col:
        if st.session_state.get("confirm_quit_app", False):
            if st.button("Confirm Quit", type="primary"):
                st.session_state.confirm_quit_app = False
                st.session_state.quit_app_requested = True
                st.rerun()
            if st.button("Cancel"):
                st.session_state.confirm_quit_app = False
                st.rerun()
        else:
            if st.button("Quit App"):
                st.session_state.confirm_quit_app = True
                st.rerun()

    if not nupack_available:
        st.error(hf.get_nupack_install_message())

    if st.session_state.search_running or st.session_state.pilot_running or st.session_state.refine_running:
        st_autorefresh(interval=500, key="global_poll")

    st.subheader("Logs")
    log_settings_col, _ = st.columns([2, 6])
    with log_settings_col:
        with st.expander("Log View Settings", expanded=False):
            log_control_col1, log_control_col2 = st.columns([1, 1])
            with log_control_col1:
                st.number_input(
                    "Height",
                    min_value=120,
                    max_value=1200,
                    step=20,
                    key="log_console_height_px",
                    help="Visible height of the log console.",
                )
            with log_control_col2:
                st.number_input(
                    "Lines",
                    min_value=100,
                    max_value=20000,
                    step=100,
                    key="log_visible_line_count",
                    help="How many of the most recent log lines to render in the console.",
                )

    log_height_px = int(st.session_state.log_console_height_px)
    visible_line_count = int(st.session_state.log_visible_line_count)
    log_text = html.escape("\n".join(st.session_state.log_buffer[-visible_line_count:]))
    st.html(
        f"""
        <div
          id="log-console"
          style="
            height: {log_height_px}px;
            overflow-y: auto;
            white-space: pre-wrap;
            font-family: ui-monospace, SFMono-Regular, SFMono-Regular, Menlo, Monaco, Consolas, Liberation Mono, monospace;
            font-size: 0.8rem;
            line-height: 1.35;
            border: 1px solid rgba(49, 51, 63, 0.2);
            border-radius: 0.5rem;
            padding: 0.75rem;
            background: white;
            color: rgb(49, 51, 63);
            box-sizing: border-box;
          "
        >{log_text}</div>
        <script>
        const logConsole = document.getElementById("log-console");
        if (logConsole) {{
          logConsole.scrollTop = logConsole.scrollHeight;
        }}
        </script>
        """,
        width="stretch",
        unsafe_allow_javascript=True,
    )

    # 3. Sidebar: Global Settings
    st.sidebar.header("Global Settings")
    st.sidebar.subheader("Sequence Layout")
    graphic_path = Path(__file__).with_name("graphics") / "on_target.png"
    st.sidebar.image(str(graphic_path), width="content")

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
    random_seed = st.sidebar.number_input(
        "Random Seed",
        value=42,
        disabled=st.session_state.busy,
        label_visibility="collapsed",
    )

    @st.cache_data(show_spinner=False)
    def _cached_seqwalk_cores(length, k, rcfree, seed):
        try:
            from seqwalk import design
        except ImportError as exc:
            raise RuntimeError("SeqWalk is required for this mode. Install it with `pip install seqwalk`.") from exc

        random_state = None
        if seed is not None:
            random_state = random.getstate()
            random.seed(int(seed))

        try:
            return list(
                design.max_size(
                    int(length),
                    int(k),
                    alphabet="ACGT",
                    RCfree=bool(rcfree),
                )
            )
        finally:
            if random_state is not None:
                random.setstate(random_state)

    st.sidebar.subheader("SeqWalk")
    seqwalk_available = importlib.util.find_spec("seqwalk") is not None
    if not seqwalk_available and st.session_state.use_seqwalk:
        st.session_state.use_seqwalk = False

    use_seqwalk = st.sidebar.checkbox(
        "Use SeqWalk Cores",
        key="use_seqwalk",
        disabled=(st.session_state.busy or not seqwalk_available),
    )
    if not seqwalk_available:
        st.sidebar.caption(
            "Optional dependency not installed. Install SeqWalk separately if you want SeqWalk-backed cores."
        )
    st.session_state.seqwalk_k = max(1, min(int(st.session_state.seqwalk_k), int(seq_length)))
    seqwalk_k = st.sidebar.number_input(
        "SeqWalk k",
        min_value=1,
        max_value=int(seq_length),
        key="seqwalk_k",
        disabled=(st.session_state.busy or not use_seqwalk or not seqwalk_available),
    )
    seqwalk_rcfree = st.sidebar.checkbox(
        "RCfree",
        key="seqwalk_rcfree",
        disabled=(st.session_state.busy or not use_seqwalk or not seqwalk_available),
    )
    seqwalk_cores = None
    seqwalk_error = None

    if use_seqwalk and seqwalk_available:
        try:
            seqwalk_cores = _cached_seqwalk_cores(
                length=int(seq_length),
                k=int(seqwalk_k),
                rcfree=bool(seqwalk_rcfree),
                seed=int(random_seed),
            )
        except Exception as exc:
            seqwalk_error = str(exc)
            st.sidebar.error(seqwalk_error)
        else:
            st.sidebar.caption(f"SeqWalk cores generated: {len(seqwalk_cores)}")

    st.session_state.input_invalid = (
        not (valid_fivep and valid_threep)
        or seqwalk_error is not None
        or not nupack_available
    )

    # Registry Factory helper
    def get_registry():
        if use_seqwalk and seqwalk_error is not None:
            raise RuntimeError(seqwalk_error)

        registry = sc.SequencePairRegistry(
            length=seq_length,
            fivep_ext=fivep_ext,
            threep_ext=threep_ext,
            unwanted_substrings=unwanted,
            apply_unwanted_to=apply_to,
            seed=random_seed,
            preselected_cores=seqwalk_cores if use_seqwalk else None,
        )
        registry.use_seqwalk = bool(use_seqwalk)
        registry.seqwalk_k = int(seqwalk_k) if use_seqwalk else None
        registry.seqwalk_rcfree = bool(seqwalk_rcfree) if use_seqwalk else None
        registry.seqwalk_core_count = len(seqwalk_cores) if use_seqwalk and seqwalk_cores is not None else None
        return registry

    def sync_nupack_params():
        hf.set_nupack_params(
            material=material,
            celsius=celsius,
            sodium=sodium,
            magnesium=magnesium
        )
        hf.set_energy_type("total")

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
        ["1. Selection Helper", "2. Pilot Analysis", "3. Off-Target Limit", "4. Sequence Search", "5. Load Results"],
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
    elif nav == "4. Sequence Search":
        render_search_tab(get_registry, nupack_params)
    else:
        render_load_results_tab(nupack_available)
