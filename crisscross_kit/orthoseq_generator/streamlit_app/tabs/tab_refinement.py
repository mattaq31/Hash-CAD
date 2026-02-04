import streamlit as st
import random
import threading
from orthoseq_generator import sequence_computations as sc
from orthoseq_generator.streamlit_app import plotly_utils as pu

def _refine_worker(registry, min_on, max_on, refine_size, out_q):
    try:
        subset, indices = sc.select_subset_in_energy_range(
            registry,
            energy_min=float(min_on),
            energy_max=float(max_on),
            max_size=refine_size,
            Use_Library=False
        )

        if not subset:
            out_q.put(("done", None, None, "No sequences found in the specified on-target range."))
            return

        on_e = sc.compute_ontarget_energies(subset)
        off_e = sc.compute_offtarget_energies(subset)
        out_q.put(("done", on_e, off_e, None))
    except Exception as e:
        out_q.put(("done", None, None, repr(e)))

def render_refinement_tab(registry_factory, nupack_params):
    st.header("Step 2: Off-Target Threshold Selection")

    if st.session_state.run_compute_2 and not st.session_state.refine_running:
        st.session_state.run_compute_2 = False

        random.seed(nupack_params['random_seed'])
        nupack_params['sync_func']()

        if st.session_state.registry is None:
            st.session_state.registry = registry_factory()

        st.session_state.refine_running = True

        t = threading.Thread(
            target=_refine_worker,
            args=(
                st.session_state.registry,
                float(st.session_state.min_ontarget),
                float(st.session_state.max_ontarget),
                int(st.session_state.refine_size),
                st.session_state.refine_queue,
            ),
            daemon=True
        )
        st.session_state.refine_thread = t
        t.start()

        st.rerun()

    if st.session_state.refine_running and (not st.session_state.refine_queue.empty()):
        msg, on_e, off_e, err = st.session_state.refine_queue.get()

        st.session_state.refine_running = False
        st.session_state.busy = False

        if err is not None:
            st.session_state.on_e_range = None
            st.session_state.off_e_range = None
            st.error(f"Refinement analysis failed: {err}")
        else:
            st.session_state.on_e_range = on_e
            st.session_state.off_e_range = off_e

        st.rerun()

    st.write("On-target range is fixed from Tab 1. Choose the off-target limit here, then commit for Tab 3.")

    # Read-only display of committed on-target range
    st.info(
        f"Fixed on-target range (committed from Tab 1): "
        f"[{st.session_state.min_ontarget:.2f}, {st.session_state.max_ontarget:.2f}] kcal/mol"
    )

    refine_size = st.number_input(
        "Refinement Sample Size", 
        min_value=10, 
        max_value=1000, 
        value=50, 
        key="refine_size", 
        disabled=st.session_state.busy
    )

    if st.button("Run Refinement Analysis", key="btn_run_refine", disabled=st.session_state.busy):
        st.session_state.run_compute_2 = True
        st.session_state.busy = True
        st.rerun()

    if st.session_state.refine_running:
        st.info("Refinement analysis running…")

    if (
            st.session_state.on_e_range is not None
            and st.session_state.off_e_range is not None
    ):
        st.markdown("---")
        st.subheader("Select Off-Target Energy Threshold (Draft)")
        st.write("Set max Off-Target Energy Threshold")

        # Draft off-target input + commit button
        col_x, col_y = st.columns([1, 1])
        with col_x:
            st.number_input(
                "Draft Off-Target Limit (kcal/mol)",
                step=None,
                key="draft_offtarget_limit",
                disabled=st.session_state.busy
            )
        with col_y:
            if st.button("Commit off-target limit → Tab 3", key="btn_commit_offtarget", disabled=st.session_state.busy):
                st.session_state.offtarget_limit = float(st.session_state.draft_offtarget_limit)
                st.success("Committed. Tab 3 now uses this off-target limit.")

        fig = pu.create_interactive_histogram(
            st.session_state.on_e_range,
            st.session_state.off_e_range,
            float(st.session_state.min_ontarget),          # fixed
            float(st.session_state.max_ontarget),          # fixed
            off_limit=float(st.session_state.draft_offtarget_limit)  # draft, editable field above
        )
        st.plotly_chart(fig, width="stretch", key="refine_chart_static")
