import tempfile
from datetime import datetime
from pathlib import Path

import streamlit as st

from orthoseq_generator import helper_functions as hf
from orthoseq_generator import sequence_computations as sc
from orthoseq_generator.energy_plots import plot_on_off_target_histograms, plot_self_energy_histogram
from orthoseq_generator.search_report_reader import load_found_pairs, load_metadata
from orthoseq_generator.streamlit_app import plotly_utils as pu


def render_load_results_tab(nupack_available=True):
    st.header("Load Existing Results")
    st.write("Load a saved XLSX search report and recreate the energy plots.")

    uploaded_report = st.file_uploader(
        "Search report (.xlsx)",
        type=["xlsx"],
        key="uploaded_search_report_xlsx",
        disabled=st.session_state.search_running or st.session_state.busy,
    )

    if st.button(
        "Plot Uploaded Report",
        key="btn_plot_uploaded_report",
        disabled=(
            uploaded_report is None
            or st.session_state.search_running
            or st.session_state.busy
            or not nupack_available
        ),
    ):
        st.session_state.busy = True
        st.session_state.loaded_report_error = None

        temp_report_path = None
        previous_nupack = hf.NUPACK_PARAMS.copy()
        try:
            with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
                tmp.write(uploaded_report.getvalue())
                temp_report_path = Path(tmp.name)

            found_pairs = load_found_pairs(temp_report_path)
            metadata = load_metadata(temp_report_path)
            sequence_pairs = list(zip(found_pairs["seq"], found_pairs["rc_seq"]))

            hf.set_nupack_params(
                material=metadata["nupack.material"],
                celsius=metadata["nupack.celsius"],
                sodium=metadata["nupack.sodium"],
                magnesium=metadata["nupack.magnesium"],
            )

            on_e, self_e_seq, self_e_rc_seq = sc.compute_ontarget_energies(sequence_pairs)
            off_e = sc.compute_offtarget_energies(sequence_pairs)

            min_on = metadata.get("search.min_ontarget")
            max_on = metadata.get("search.max_ontarget")
            off_limit = metadata.get("search.offtarget_limit")
            self_limit = metadata.get("search.self_energy_limit")

            st.session_state.loaded_report_fig = pu.create_interactive_histogram(
                on_e,
                off_e,
                float(min_on),
                float(max_on),
                off_limit=float(off_limit) if off_limit is not None else None,
            )
            st.session_state.loaded_report_self_fig = pu.create_self_energy_histogram(
                [self_e_seq, self_e_rc_seq],
                self_limit=float(self_limit) if self_limit is not None else None,
            )

            results_dir = Path(hf.get_default_results_folder())
            artifact_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            report_stem = Path(uploaded_report.name).stem
            on_off_pdf_path = results_dir / f"{report_stem}_on_off_target_{artifact_timestamp}.pdf"
            self_pdf_path = results_dir / f"{report_stem}_self_energy_{artifact_timestamp}.pdf"

            plot_on_off_target_histograms(
                on_e,
                off_e,
                output_path=on_off_pdf_path,
                show_plot=False,
                vlines={"min_ontarget": float(min_on)} if min_on is not None else None,
            )
            plot_self_energy_histogram(
                (self_e_seq, self_e_rc_seq),
                output_path=self_pdf_path,
                show_plot=False,
            )

            st.session_state.loaded_report_metadata = metadata
            st.session_state.loaded_report_name = uploaded_report.name
            st.session_state.loaded_report_pair_count = len(sequence_pairs)
            st.session_state.loaded_report_on_off_pdf_path = str(on_off_pdf_path)
            st.session_state.loaded_report_self_pdf_path = str(self_pdf_path)
        except Exception as e:
            st.session_state.loaded_report_metadata = None
            st.session_state.loaded_report_name = None
            st.session_state.loaded_report_pair_count = None
            st.session_state.loaded_report_fig = None
            st.session_state.loaded_report_self_fig = None
            st.session_state.loaded_report_on_off_pdf_path = None
            st.session_state.loaded_report_self_pdf_path = None
            st.session_state.loaded_report_error = str(e)
        finally:
            hf.set_nupack_params(
                material=previous_nupack["MATERIAL"],
                celsius=previous_nupack["CELSIUS"],
                sodium=previous_nupack["SODIUM"],
                magnesium=previous_nupack["MAGNESIUM"],
            )
            if temp_report_path is not None and temp_report_path.exists():
                temp_report_path.unlink()
            st.session_state.busy = False
        st.rerun()

    if st.session_state.search_running:
        st.caption("Disabled while a search is running.")

    if st.session_state.loaded_report_error:
        st.error(f"Failed to load report: {st.session_state.loaded_report_error}")

    if st.session_state.loaded_report_metadata is not None:
        metadata = st.session_state.loaded_report_metadata
        nupack_lines = [
            f"Material: {metadata['nupack.material']}",
            f"Temperature (C): {metadata['nupack.celsius']}",
            f"Sodium (M): {metadata['nupack.sodium']}",
            f"Magnesium (M): {metadata['nupack.magnesium']}",
        ]
        criteria_lines = []
        if metadata.get("search.min_ontarget") is not None and metadata.get("search.max_ontarget") is not None:
            criteria_lines.append(
                f"On-target energy range: "
                f"[{metadata['search.min_ontarget']}, {metadata['search.max_ontarget']}] kcal/mol"
            )
        if metadata.get("search.offtarget_limit") is not None:
            criteria_lines.append(f"Off-target energy limit: {metadata['search.offtarget_limit']} kcal/mol")
        if metadata.get("search.self_energy_limit") is not None:
            criteria_lines.append(
                f"Secondary-structure energy limit: {metadata['search.self_energy_limit']} kcal/mol"
            )
        if metadata.get("search.random_seed") is not None:
            criteria_lines.append(f"Random seed: {metadata['search.random_seed']}")
        if metadata.get("search.initial_fresh_pair_count") is not None:
            criteria_lines.append(
                f"Initial graph search subset size: {metadata['search.initial_fresh_pair_count']}"
            )
        if metadata.get("search.vc_max_iterations") is not None:
            criteria_lines.append(f"Graph search iterations: {metadata['search.vc_max_iterations']}")
        if metadata.get("search.prune_fraction") is not None:
            criteria_lines.append(f"Perturbation fraction: {metadata['search.prune_fraction']}")

        st.info("NUPACK parameters:\n\n" + "\n\n".join(nupack_lines))
        if criteria_lines:
            st.info("Search criteria:\n\n" + "\n\n".join(criteria_lines))
        st.caption(
            "  \n".join(
                [
                    f"Report file: {st.session_state.loaded_report_name}",
                    f"Found sequence pairs: {st.session_state.loaded_report_pair_count}",
                    f"Saved on/off-target PDF: {st.session_state.loaded_report_on_off_pdf_path}",
                    f"Saved self-energy PDF: {st.session_state.loaded_report_self_pdf_path}",
                ]
            )
        )

    if st.session_state.loaded_report_fig is not None:
        st.plotly_chart(
            st.session_state.loaded_report_fig,
            width="stretch",
            key="loaded_report_chart_static",
        )
    if st.session_state.loaded_report_self_fig is not None:
        st.plotly_chart(
            st.session_state.loaded_report_self_fig,
            width="stretch",
            key="loaded_report_self_chart_static",
        )
