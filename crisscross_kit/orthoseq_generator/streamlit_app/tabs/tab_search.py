import streamlit as st
import random
import threading
import time
from pathlib import Path
from orthoseq_generator import helper_functions as hf
from orthoseq_generator.search_algorithm import hybrid_search
from orthoseq_generator.search_reporting import (
    build_selected_sequence_data,
    validate_selected_pairs,
    verify_selected_pairs,
    write_hybrid_search_result_xlsx,
)
from orthoseq_generator.streamlit_app import plotly_utils as pu

def _search_worker(
    registry,
    offtarget_limit,
    max_on,
    min_on,
    self_energy_limit,
    initial_fresh_pair_count,
    vc_max_iterations,
    prune_fraction,
    stop_event,
    out_q,
    progress_report_interval_min=None,
):
    start_time = time.time()
    try:
        res = hybrid_search(
            registry,
            offtarget_limit,
            max_on,
            min_on,
            self_energy_limit,
            initial_fresh_pair_count=initial_fresh_pair_count,
            vc_max_iterations=vc_max_iterations,
            prune_fraction=prune_fraction,
            stop_event=stop_event,
            return_diagnostics=True,
            progress_report_interval_min=progress_report_interval_min,
        )
        if not res["final_pairs"]:
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
    with st.expander("Advanced Search Parameters", expanded=False):
        st.number_input(
            "Initial Subset Size",
            min_value=1,
            value=st.session_state.subset_size_search,
            key="subset_size_search",
            disabled=st.session_state.search_running,
            help="Number of sequence pairs collected in the seed pass before the first vertex-cover run."
        )
        st.number_input(
            "Vertex-Cover Max Iterations",
            min_value=1,
            value=st.session_state.search_vc_max_iterations,
            key="search_vc_max_iterations",
            disabled=st.session_state.search_running,
            help="Number of refinement iterations used inside each graph-based optimization run."
        )
        st.number_input(
            "Prune Fraction",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.search_prune_fraction,
            step=0.05,
            key="search_prune_fraction",
            disabled=st.session_state.search_running,
            help="Controls how strongly the current graph-based solution is perturbed before it is refined again."
        )
        st.number_input(
            "Progress Report Interval (min)",
            min_value=0,
            value=st.session_state.search_progress_interval_min,
            key="search_progress_interval_min",
            disabled=st.session_state.search_running,
            help="During collection, report estimated pair count at this interval. 0 = disabled."
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
        st.session_state.search_run_data = None
        st.session_state.search_duration = 0.0
        st.session_state.search_report_path = None

        # Reset final-plot cache for new run
        st.session_state.final_cache_ready = False
        st.session_state.final_fig = None
        st.session_state.final_self_fig = None

        registry = st.session_state.registry
        offtarget_limit = float(st.session_state.offtarget_limit)
        max_on = float(st.session_state.max_ontarget)
        min_on = float(st.session_state.min_ontarget)
        self_energy_limit = float(st.session_state.self_energy_limit)
        initial_fresh_pair_count = int(st.session_state.subset_size_search)
        vc_max_iterations = int(st.session_state.search_vc_max_iterations)
        prune_fraction = float(st.session_state.search_prune_fraction)
        progress_interval_raw = int(st.session_state.search_progress_interval_min)
        progress_report_interval_min = progress_interval_raw if progress_interval_raw > 0 else None
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
                initial_fresh_pair_count,
                vc_max_iterations,
                prune_fraction,
                stop_event,
                out_q,
                progress_report_interval_min,
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
            st.session_state.search_run_data = None
            st.session_state.search_error = err
        else:
            st.session_state.search_completed = True
            st.session_state.search_run_data = res
            st.session_state.orthogonal_seq_pairs = res["final_pairs"]
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

        if not st.session_state.final_cache_ready:
            st.session_state.busy = True
            with st.spinner("Computing final energies for visualization..."):
                search_run_data = st.session_state.search_run_data
                selected_sequence_data = build_selected_sequence_data(
                    orthogonal_seq_pairs,
                    search_run_data["final_pair_ids"],
                )
                verified = verify_selected_pairs(
                    selected_sequence_data,
                    nupack_params=search_run_data["nupack"],
                )
                validation_data = validate_selected_pairs(
                    selected_sequence_data,
                    verified,
                    min_ontarget=float(st.session_state.min_ontarget),
                    max_ontarget=float(st.session_state.max_ontarget),
                    self_energy_limit=float(st.session_state.self_energy_limit),
                    offtarget_limit=float(st.session_state.offtarget_limit),
                )
                seed_sequence_data = build_selected_sequence_data(
                    search_run_data["seed_pairs"],
                    search_run_data["seed_pair_ids"],
                )
                seed_verified = search_run_data["seed_verified"]
                results_dir = Path(hf.get_default_results_folder())
                report_path = write_hybrid_search_result_xlsx(
                    results_dir / "ortho_sequences_ui.xlsx",
                    algorithm_name="hybrid_search",
                    selected_sequence_data=selected_sequence_data,
                    verified=verified,
                    search_params={
                        **search_run_data["search_params"],
                        "random_seed": nupack_params["random_seed"],
                        "total_nupack_calls": search_run_data["total_nupack_calls"],
                        "search_duration_s": st.session_state.search_duration,
                    },
                    input_params={"source_kind": "on_the_fly_registry", **search_run_data["sequence_source"]},
                    artifact_info={"dataset_dir": None, "dataset_toml": None, "dataset_npz": None},
                    nupack_params=search_run_data["nupack"],
                    generation_data=search_run_data["generation_data"],
                    validation_data=validation_data,
                    seed_sequence_data=seed_sequence_data,
                    seed_verified=seed_verified,
                    dataset_info={},
                    extra_metadata={
                        "best_generation_result_size": len(selected_sequence_data),
                        "stopped_reason": search_run_data["stopped_reason"],
                    },
                )
                st.session_state.search_report_path = report_path

                st.session_state.final_fig = pu.create_interactive_histogram(
                    verified["on_target_energies"],
                    verified["off_target"],
                    float(st.session_state.min_ontarget),
                    float(st.session_state.max_ontarget),
                    off_limit=float(st.session_state.offtarget_limit)
                )
                st.session_state.final_self_fig = pu.create_self_energy_histogram(
                    [verified["self_energy_seqs"], verified["self_energy_rc_seqs"]],
                    self_limit=float(st.session_state.self_energy_limit)
                )
                st.session_state.final_cache_ready = True
                st.session_state.busy = False
            st.rerun()

        if st.session_state.search_report_path:
            with open(st.session_state.search_report_path, "rb") as f:
                st.download_button(
                    label="Download Sequences",
                    data=f.read(),
                    file_name="ortho_sequences.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    disabled=st.session_state.search_running
                )

        if st.session_state.final_fig is not None:
            st.plotly_chart(st.session_state.final_fig, width="stretch", key="final_chart_static")
        if st.session_state.final_self_fig is not None:
            st.plotly_chart(st.session_state.final_self_fig, width="stretch", key="final_self_chart_static")
