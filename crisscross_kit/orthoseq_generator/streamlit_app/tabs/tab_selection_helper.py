import math
import numpy as np
import plotly.graph_objects as go
import streamlit as st

R_KCAL = 1.98720425864083e-3
RHO_H2O = 55.14


def _solve_ab_equilibrium(a0, b0, kc):
    a = kc
    b = -(kc * (a0 + b0) + 1.0)
    c = kc * a0 * b0
    disc = b * b - 4.0 * a * c
    disc = max(disc, 0.0)
    x = (-b - math.sqrt(disc)) / (2.0 * a)
    return x


def _fraction_bound_from_dg(dg_assoc, conc_m, temp_c):
    if conc_m <= 0.0:
        return 0.0
    rt = R_KCAL * (273.15 + temp_c)
    kx = math.exp(-dg_assoc / rt)
    kc = kx / RHO_H2O
    ab = _solve_ab_equilibrium(conc_m, conc_m, kc)
    return max(min(ab / conc_m, 1.0), 0.0)


def _make_line_plot(x_vals, y_vals, title, x_label, y_label, x_range=None):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x_vals,
        y=y_vals,
        mode="lines",
        line=dict(color="#1f77b4", width=3),
        hovertemplate=f"{x_label}=%{{x:.3f}}<br>{y_label}=%{{y:.4f}}<extra></extra>",
    ))

    fig.update_layout(
        title=title,
        xaxis_title=x_label,
        yaxis_title=y_label,
        template="plotly_white",
        dragmode="zoom",
        hovermode="x unified",
    )

    fig.update_xaxes(showspikes=True, spikemode="across", spikesnap="cursor")
    fig.update_yaxes(showspikes=False, fixedrange=True)
    if x_range is not None:
        fig.update_xaxes(range=x_range)
    return fig


def render_selection_helper_tab(nupack_params):
    st.header("Selection Helper")
    st.write("Reference plots relating energy values to strand binding and secondary-structure formation.")

    temp_c = float(nupack_params["celsius"])
    st.caption(f"Using temperature: T= 273.15K + {temp_c:.1f}K")

    st.subheader("Strand Binding")

    st.markdown(
        r"""
    Association reaction of two strands $A$ and $B$ forming a complex $C$:

    $$
    A + B \rightleftharpoons C
    $$

    Fraction $P_b$ of strand $A$ bound in complex $C$:

    $$
    P_b = \frac{[C]}{[A_0]}
    = \frac{(2\alpha + 1) - \sqrt{1 + 4\alpha}}{2\alpha},
    \qquad
    \alpha = K [A_0],
    \qquad
    K = \frac{\exp\!\left(-\Delta G_{\mathrm{assoc}} / RT\right)}{\rho_{\mathrm{H_2O}}}
    $$
    """
    )
    st.caption(
        r" Total strand concentrations: $[A_0]=[B_0]$, "
        r" Unbound strand concentrations: $[A]=[B]$, "
        r"Complex concentration: $[C]$, "
        r" Molarity of water: $\rho_{\mathrm{H_2O}}=55.14 \mathrm{mol\,L^{-1}}$,  "
        r"Gibbs free energy of association: $\Delta G_{\mathrm{assoc}}$."
    )

    st.caption(
        r"The Gibbs free energy of association is defined as "
        r"$\Delta G_{\mathrm{assoc}} = G_C - (G_A + G_B)$, "
        r"where $G_C$, $G_A$, and $G_B$ are the standard Gibbs free energies "
        r"of the complex and unbound strands, respectively. "
        r"The algorithm uses $\Delta G_{\mathrm{assoc}}$ as a selection criterion. "
        r"$G_C$, $G_A$, and $G_B$ are computed using NUPACK. "
        r"The molarity of water is used to convert from mole fractions (assumed by NUPACK) to molar concentrations. "

    )

    conc_nm = st.number_input(
        "Strand concentrations (nM)",
        min_value=0.0,
        value=1000.0,
        step=10.0,
        format="%.1f",
        key="selection_helper_conc_nm",
        disabled=st.session_state.busy,
    )

    if st.button("Plot", key="selection_helper_plot_assoc", disabled=st.session_state.busy):
        conc_m = conc_nm * 1e-9
        dg_assoc = np.linspace(0.0, -40.0, 400)
        frac_bound = np.array([
            _fraction_bound_from_dg(dg, conc_m, temp_c) for dg in dg_assoc
        ])
        st.session_state.selection_helper_assoc_fig = _make_line_plot(
            dg_assoc,
            frac_bound,
            "Strand Binding",
            "Gibbs free energy of association (kcal/mol)",
            "Fraction bound",
            x_range=[-20.0, 0.0],
        )

    if st.session_state.get("selection_helper_assoc_fig") is not None:
        st.plotly_chart(st.session_state.selection_helper_assoc_fig, width="stretch")

    st.subheader("Secondary Structure Formation")
    st.markdown(
        r"""
    Transition of a strand between the fully unpaired state $U$ and any folded
    secondary-structure state $S$:

    $$
    U \rightleftharpoons S
    $$

    Fraction $P_u$ of the strand in the fully unpaired state $U$:

    $$
    P_u
    = \frac{\exp\!\left(-G_0 / RT\right)}{\exp\!\left(-G_p / RT\right)}
    $$
    """
    )
    st.caption(
        r"Gibbs free energy of the fully unpaired state: $G_0$  "
        r"Standard Gibbs free energy of the strand: $G_p$ "
    )

    st.caption(
        r"$G_p$ corresponds to $G_A$ and $G_B$ above and is related to the partition function "
        r"$Q$ over the secondary-structure ensemble (including the unpaired state) via "
        r"$Q=\exp(-\frac{G_p}{RT})$. "
        r"$G_0=0$ is the unpaired-state reference used by NUPACK."
    )
    if st.button("Plot", key="selection_helper_plot_secondary", disabled=st.session_state.busy):
        rt = R_KCAL * (273.15 + temp_c)
        gp_vals = np.linspace(0.0, -10.0, 400)
        p_unpaired = np.exp(gp_vals / rt)
        p_unpaired = np.clip(p_unpaired, 0.0, 1.0)
        st.session_state.selection_helper_secondary_fig = _make_line_plot(
            gp_vals,
            p_unpaired,
            "Secondary Structure Formation",
            "Standard Gibbs free energy",
            "Fraction in the fully unpaired state",
            x_range=[-5.0, 0.0],
        )

    if st.session_state.get("selection_helper_secondary_fig") is not None:
        st.plotly_chart(st.session_state.selection_helper_secondary_fig, width="stretch")
