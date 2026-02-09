import streamlit as st
import random
import threading
import time
import os
from orthoseq_generator import sequence_computations as sc
from orthoseq_generator import helper_functions as hf
from orthoseq_generator.vertex_cover_algorithms import evolutionary_vertex_cover
from orthoseq_generator.streamlit_app import plotly_utils as pu

def _search_worker(
    registry,
    offtarget_limit,
    max_on,
    min_on,
    self_energy_limit,
    subsetsize,
    generations,
    stop_event,
    out_q,
):
    start_time = time.time()
    try:
        res = evolutionary_vertex_cover(
            registry,
            offtarget_limit,
            max_on,
            min_on,
            self_energy_limit,
            subsetsize=subsetsize,
            generations=generations,
            stop_event=stop_event
        )
        if not res:
            out_q.put(("done", None, time.time() - start_time, "No sequences found before termination."))
        else:
            out_q.put(("done", res, time.time() - start_time, None))
    except Exception as e:
        out_q.put(("done", None, time.time() - start_time, repr(e)))

def render_search_tab(registry_factory, nupack_params):
    st.header("Step 3: Orthogonal Sequence Search")
    st.write("All parameters are committed. Run the algorithm.")
    if st.session_state.search_error:
        st.error(f"Search failed: {st.session_state.search_error}")

    st.info(
        f"Committed on-target energy range: [{st.session_state.min_ontarget:.2f}, {st.session_state.max_ontarget:.2f}] kcal/mol\n\n"
        f"Committed off-target energy limit: {st.session_state.offtarget_limit:.2f} kcal/mol\n\n"
        f"Committed secondary-structure energy limit: {st.session_state.self_energy_limit:.2f} kcal/mol"
    )

    # Inputs (locked while running)
    st.number_input(
        "Number of New Sequence Pairs per Generation",
        value=175,
        key="subset_size_search",
        disabled=st.session_state.search_running
    )
    st.number_input(
        "Number of Generations",
        value=50,
        key="generations",
        disabled=st.session_state.search_running
    )

    col1, col2 = st.columns(2)
    final_analysis_pending = (
        st.session_state.search_completed
        and st.session_state.orthogonal_seq_pairs is not None
        and not st.session_state.final_cache_ready
    )

    # Run: set flag, one rerun
    with col1:
        if st.button(
                "Run Search",
                key="btn_run_search",
                disabled=(
                    st.session_state.search_running
                    or st.session_state.run_compute_3
                    or st.session_state.busy
                    or st.session_state.input_invalid
                    or final_analysis_pending
                )
        ):
            st.session_state.run_compute_3 = True
            st.session_state.busy = True
            st.rerun()

    # Stop: only set flags (NO warning here; warning is rendered from state below)
    with col2:
        if st.button("Stop Searching", key="btn_stop_search", disabled=not st.session_state.search_running):
            st.session_state.stop_event.set()
            st.session_state.stop_requested = True
            st.rerun()  # immediate visual update of status banner

    # ------------------------------------------------------------
    # Start thread ONCE when requested
    # ------------------------------------------------------------
    if st.session_state.run_compute_3 and not st.session_state.search_running:
        st.session_state.run_compute_3 = False
        st.session_state.search_error = None

        st.session_state.registry = registry_factory()

        random.seed(nupack_params['random_seed'])
        nupack_params['sync_func']()

        # Reset run-related state
        st.session_state.stop_requested = False
        st.session_state.stop_event.clear()
        st.session_state.search_completed = False
        st.session_state.orthogonal_seq_pairs = None
        st.session_state.search_duration = 0.0

        # Reset final-plot cache for new run
        st.session_state.final_cache_ready = False
        st.session_state.final_fig = None
        st.session_state.final_self_fig = None

        registry = st.session_state.registry
        offtarget_limit = float(st.session_state.offtarget_limit)
        max_on = float(st.session_state.max_ontarget)
        min_on = float(st.session_state.min_ontarget)
        self_energy_limit = float(st.session_state.self_energy_limit)
        subsetsize = int(st.session_state.subset_size_search)
        generations_ = int(st.session_state.generations)
        stop_event = st.session_state.stop_event
        out_q = st.session_state.search_queue
        st.session_state.search_running = True

        t = threading.Thread(
            target=_search_worker,
            args=(
                registry,
                offtarget_limit,
                max_on,
                min_on,
                self_energy_limit,
                subsetsize,
                generations_,
                stop_event,
                out_q,
            ),
            daemon=True
        )
        st.session_state.search_thread = t
        t.start()

        st.rerun()

    # ------------------------------------------------------------
    # Poll queue ONCE per rerun (autorefresh provides reruns)
    # ------------------------------------------------------------
    if st.session_state.search_running and (not st.session_state.search_queue.empty()):
        msg, res, dur, err = st.session_state.search_queue.get()

        st.session_state.search_running = False
        st.session_state.stop_requested = False
        st.session_state.busy = False

        if err is not None:
            st.session_state.search_completed = False
            st.session_state.orthogonal_seq_pairs = None
            st.session_state.search_error = err
        else:
            st.session_state.search_completed = True
            st.session_state.orthogonal_seq_pairs = res
            st.session_state.search_duration = float(dur)
            st.session_state.search_error = None

        st.rerun()

    # ------------------------------------------------------------
    # SINGLE status banner (exactly one place)
    # ------------------------------------------------------------
    if st.session_state.search_running:
        if st.session_state.stop_requested:
            st.warning("Stop requested. Waiting for the algorithm to stop…")
        else:
            st.info("Search running…")
    elif final_analysis_pending:
        st.info("Final analysis running…")

    # ------------------------------------------------------------
    # Results
    # ------------------------------------------------------------
    if st.session_state.search_completed and st.session_state.orthogonal_seq_pairs is not None:
        orthogonal_seq_pairs = st.session_state.orthogonal_seq_pairs

        st.success(f"Search completed in {st.session_state.search_duration:.2f} seconds.")
        st.write(f"Found {len(orthogonal_seq_pairs)} orthogonal sequence pairs.")

        temp_filename = "ortho_sequences_ui.txt"
        hf.save_sequence_pairs_to_txt(orthogonal_seq_pairs, filename=temp_filename)

        results_folder = hf.get_default_results_folder()
        full_temp_path = os.path.join(results_folder, temp_filename)

        with open(full_temp_path, "rb") as f:
            st.download_button(
                label="Download Orthogonal Sequences",
                data=f,
                file_name="ortho_sequences.txt",
                mime="text/plain",
                disabled=st.session_state.search_running
            )

        if not st.session_state.final_cache_ready:
            st.session_state.busy = True
            with st.spinner("Computing final energies for visualization..."):
                on_final, self_e_a, self_e_b = sc.compute_ontarget_energies(orthogonal_seq_pairs)
                off_final = sc.compute_offtarget_energies(orthogonal_seq_pairs)

                st.session_state.final_fig = pu.create_interactive_histogram(
                    on_final,
                    off_final,
                    float(st.session_state.min_ontarget),
                    float(st.session_state.max_ontarget),
                    off_limit=float(st.session_state.offtarget_limit)
                )
                st.session_state.final_self_fig = pu.create_self_energy_histogram(
                    [self_e_a, self_e_b],
                    self_limit=float(st.session_state.self_energy_limit)
                )
                st.session_state.final_cache_ready = True
                st.session_state.busy = False
            st.rerun()

        if st.session_state.final_fig is not None:
            st.plotly_chart(st.session_state.final_fig, width="stretch", key="final_chart_static")
        if st.session_state.final_self_fig is not None:
            st.plotly_chart(st.session_state.final_self_fig, width="stretch", key="final_self_chart_static")
