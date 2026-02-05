import streamlit as st
import random
import threading
from orthoseq_generator import sequence_computations as sc
from orthoseq_generator.streamlit_app import plotly_utils as pu
from orthoseq_generator.streamlit_app.state_manager import START_MIN_ON, START_MAX_ON

def _pilot_worker(registry, pilot_size, out_q):
    try:
        subset = sc.select_subset(registry, max_size=pilot_size)
        on_e, self_e_a, self_e_b = sc.compute_ontarget_energies(subset)
        off_e = sc.compute_offtarget_energies(subset)
        out_q.put(("done", on_e, off_e, (self_e_a, self_e_b), None))
    except Exception as e:
        out_q.put(("done", None, None, None, repr(e)))

def render_exploratory_tab(registry_factory, nupack_params):
    st.header("Step 1: Pilot Analysis")

    if st.session_state.get("sync_self_energy_draft", False) or "draft_self_energy_limit_input" not in st.session_state:
        st.session_state.draft_self_energy_limit_input = float(st.session_state.self_energy_limit)
        st.session_state.sync_self_energy_draft = False

    if st.session_state.run_compute_1 and not st.session_state.pilot_running:
        st.session_state.run_compute_1 = False

        random.seed(nupack_params['random_seed'])
        nupack_params['sync_func']()

        registry = registry_factory()
        st.session_state.registry = registry

        st.session_state.pilot_running = True

        t = threading.Thread(
            target=_pilot_worker,
            args=(registry, int(st.session_state.pilot_size), st.session_state.pilot_queue),
            daemon=True
        )
        st.session_state.pilot_thread = t
        t.start()

        st.rerun()

    if st.session_state.pilot_running and (not st.session_state.pilot_queue.empty()):
        msg, on_e, off_e, self_e, err = st.session_state.pilot_queue.get()

        st.session_state.pilot_running = False
        st.session_state.busy = False

        if err is not None:
            st.session_state.on_e_pilot = None
            st.session_state.off_e_pilot = None
            st.session_state.self_e_pilot = None
            st.error(f"Pilot analysis failed: {err}")
        else:
            st.session_state.on_e_pilot = on_e
            st.session_state.off_e_pilot = off_e
            st.session_state.self_e_pilot = self_e

        st.rerun()

    st.write("Generate a random sample of sequence pairs to see the general energy distribution.")

    pilot_size = st.number_input(
        "Pilot Sample Size", 
        min_value=10, 
        max_value=1000, 
        value=50, 
        key="pilot_size", 
        disabled=st.session_state.busy
    )

    if st.button("Run Pilot Analysis", key="btn_run_pilot", disabled=st.session_state.busy):
        st.session_state.run_compute_1 = True
        st.session_state.busy = True
        st.rerun()

    if st.session_state.pilot_running:
        st.info("Pilot analysis running…")

    if (
            st.session_state.on_e_pilot is not None
            and st.session_state.off_e_pilot is not None
    ):
        st.markdown("---")
        st.subheader("Select On-Target Energy Range (Draft)")
        st.write("Set min and max manually. Then commit it for Tab 2.")

        col_a, col_b, col_c = st.columns([1, 1, 1])

        with col_a:
            st.number_input(
                "Min On-Target (kcal/mol)",
                step=None,
                key="draft_min_ontarget",
                value=START_MIN_ON,
                disabled=st.session_state.busy
            )

        with col_b:
            st.number_input(
                "Max On-Target (kcal/mol)",
                step=None,
                key="draft_max_ontarget",
                value=START_MAX_ON,
                disabled=st.session_state.busy
            )

        with col_c:
            if st.button("Use This Range", key="btn_commit_range", disabled=st.session_state.busy):
                a = float(st.session_state.draft_min_ontarget)
                b = float(st.session_state.draft_max_ontarget)

                st.session_state.min_ontarget = min(a, b)
                st.session_state.max_ontarget = max(a, b)

                st.success("Range Transferred to Tab 2")

        # Plot reflects draft range
        fig = pu.create_interactive_histogram(
            st.session_state.on_e_pilot,
            st.session_state.off_e_pilot,
            float(st.session_state.draft_min_ontarget),
            float(st.session_state.draft_max_ontarget),
        )
        st.plotly_chart(fig, width="stretch", key="pilot_chart_static")

        if st.session_state.self_e_pilot is not None:
            st.markdown("---")
            st.subheader("Select Self-Energy Limit (Draft)")
            st.write("Set a minimum self-energy threshold, then commit it for Tabs 2 and 3.")

            col_s1, col_s2 = st.columns([1, 1])
            with col_s1:
                st.number_input(
                    "Draft Self-Energy Limit (kcal/mol)",
                    step=None,
                    key="draft_self_energy_limit_input",
                    disabled=st.session_state.busy
                )
            with col_s2:
                if st.button("Use This Self-Energy Limit", key="btn_commit_self_energy", disabled=st.session_state.busy):
                    committed_limit = float(st.session_state.draft_self_energy_limit_input)
                    st.session_state.self_energy_limit = committed_limit
                    st.session_state.sync_self_energy_draft = True
                    st.success("Self-energy limit transferred to Tabs 2 and 3.")
                    #st.rerun()

            self_fig = pu.create_self_energy_histogram(
                st.session_state.self_e_pilot,
                self_limit=float(st.session_state.draft_self_energy_limit_input)
            )
            st.plotly_chart(self_fig, width="stretch", key="pilot_self_chart_static")
