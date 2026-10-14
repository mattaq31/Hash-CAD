import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

def create_interactive_histogram(
    on_energies, off_energies, min_on, max_on, off_limit=None, bins=80, crossref_energies=None,
):
    """Build the original histogram, optionally adding an external distribution with linked x-axes."""
    crossref = np.asarray(crossref_energies if crossref_energies is not None else [], dtype=float).ravel()
    if not np.isfinite(crossref).all():
        raise ValueError("Cross-reference energies must all be finite before plotting.")
    if isinstance(off_energies, dict):
        off_energies = np.concatenate([
            off_energies['handle_handle_energies'].flatten(),
            off_energies['antihandle_handle_energies'].flatten(),
            off_energies['antihandle_antihandle_energies'].flatten()
        ])
        off_energies = off_energies[off_energies != 0]

    combined_min = min(np.min(on_energies), np.min(off_energies))
    combined_max = max(np.max(on_energies), np.max(off_energies))
    if crossref.size:
        combined_min = min(combined_min, float(crossref.min()))
        combined_max = max(combined_max, float(crossref.max()))

    combined_min = min(combined_min, min_on - 1)
    combined_max = max(combined_max, max_on + 1)
    if off_limit is not None:
        combined_min = min(combined_min, off_limit - 1)
        combined_max = max(combined_max, off_limit + 1)

    fig = go.Figure()

    fig.add_trace(go.Histogram(
        x=off_energies,
        xbins=dict(start=combined_min, end=combined_max, size=(combined_max - combined_min) / bins),
        name='Off-target',
        marker_color='#d62728',
        opacity=0.75,
        histnorm='probability density'
    ))

    fig.add_trace(go.Histogram(
        x=on_energies,
        xbins=dict(start=combined_min, end=combined_max, size=(combined_max - combined_min) / bins),
        name='On-target',
        marker_color='#1f77b4',
        opacity=0.75,
        histnorm='probability density'
    ))



    # IMPORTANT: true vertical vlines spanning full height in paper coords
    shapes = [
        dict(
            type='line',
            xref='x',
            yref='paper',
            x0=float(min_on), x1=float(min_on),
            y0=0, y1=1,
            line=dict(color='blue', width=3, dash='dash'),
            name='min_on',
        ),
        dict(
            type='line',
            xref='x',
            yref='paper',
            x0=float(max_on), x1=float(max_on),
            y0=0, y1=1,
            line=dict(color='blue', width=3, dash='dash'),
            name='max_on',
        )
    ]

    if off_limit is not None:
        shapes.append(
            dict(
                type='line',
                xref='x',
                yref='paper',
                x0=float(off_limit), x1=float(off_limit),
                y0=0, y1=1,
                line=dict(color='red', width=3, dash='dash'),
                name='off_limit',
            )
        )

    # --- add invisible dense x trace for smooth hover readout ---
    x_dense = np.linspace(combined_min, combined_max, 5000)
    fig.add_trace(go.Scatter(
        x=x_dense,
        y=np.zeros_like(x_dense),
        mode="lines",
        line=dict(width=0),
        opacity=0,
        showlegend=False,
        hovertemplate="x=%{x:.3f}<extra></extra>",
    ))

    fig.update_layout(
        shapes=shapes,
        barmode="overlay",
        title="On-target vs Off-target Energy Distribution",
        xaxis_title="Gibbs free energy (kcal/mol)",
        yaxis_title="Normalized frequency",
        template="plotly_white",

        # no selection / no drawing
        dragmode="zoom",
        hovermode="x unified"
    )

    # cursor line that follows the mouse (x only)
    fig.update_xaxes(showspikes=True, spikemode="across", spikesnap="cursor")
    fig.update_yaxes(showspikes=False)

    # keep y axis fixed if you want
    fig.update_xaxes(fixedrange=False)
    fig.update_yaxes(fixedrange=True)

    if crossref.size:
        # A single Plotly figure links zoom/pan natively. Keep the original
        # figure untouched when no reference energies are present.
        fig = make_subplots(
            rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.15, figure=fig,
            subplot_titles=("", "External Crossreference Energy Distribution"),
        )
        for shape in fig.layout.shapes:
            shape.yref = "y domain"
        fig.add_trace(go.Histogram(
            x=crossref,
            xbins=dict(start=combined_min, end=combined_max, size=(combined_max - combined_min) / bins),
            name="External crossreference", marker_color="#2ca02c", opacity=0.75,
            histnorm="probability density",
        ), row=2, col=1)
        if off_limit is not None:
            fig.add_shape(
                type="line", xref="x2", yref="y2 domain", x0=float(off_limit), x1=float(off_limit),
                y0=0, y1=1, line=dict(color="red", width=3, dash="dash"), name="off_limit",
            )
        fig.update_xaxes(
            range=[combined_min, combined_max], showticklabels=True, fixedrange=False,
            showspikes=True, spikemode="across", spikesnap="cursor",
        )
        fig.update_yaxes(showspikes=False, fixedrange=True)
        fig.update_layout(
            height=850, xaxis2_title="Gibbs free energy (kcal/mol)", yaxis2_title="Normalized frequency",
        )

    return fig


def create_self_energy_histogram(self_energies, self_limit=None, bins=60):
    if isinstance(self_energies, dict):
        values = [np.ravel(v) for v in self_energies.values()]
        combined = np.concatenate(values) if values else np.array([])
    elif isinstance(self_energies, (list, tuple)) and len(self_energies) > 1:
        combined = np.concatenate([np.ravel(v) for v in self_energies])
    else:
        combined = np.ravel(self_energies)

    if combined.size == 0:
        fig = go.Figure()
        fig.update_layout(
            title="Self-Folding Energy Distribution",
            xaxis_title="Gibbs free energy (kcal/mol)",
            yaxis_title="Normalized frequency",
            template="plotly_white",
        )
        return fig

    combined_min = np.min(combined)
    combined_max = np.max(combined)
    if self_limit is not None:
        combined_min = min(combined_min, float(self_limit) - 1)
        combined_max = max(combined_max, float(self_limit) + 1)

    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=combined,
        xbins=dict(start=combined_min, end=combined_max, size=(combined_max - combined_min) / bins),
        name='Self-folding',
        marker_color='#1f77b4',
        opacity=0.75,
        histnorm='probability density'
    ))

    shapes = []
    if self_limit is not None:
        shapes.append(
            dict(
                type='line',
                xref='x',
                yref='paper',
                x0=float(self_limit), x1=float(self_limit),
                y0=0, y1=1,
                line=dict(color='blue', width=3, dash='dash'),
                name='self_limit',
            )
        )

    x_dense = np.linspace(combined_min, combined_max, 5000)
    fig.add_trace(go.Scatter(
        x=x_dense,
        y=np.zeros_like(x_dense),
        mode="lines",
        line=dict(width=0),
        opacity=0,
        showlegend=False,
        hovertemplate="x=%{x:.3f}<extra></extra>",
    ))

    fig.update_layout(
        shapes=shapes,
        barmode="overlay",
        title="Self-Folding Energy Distribution",
        xaxis_title="Gibbs free energy (kcal/mol)",
        yaxis_title="Normalized frequency",
        template="plotly_white",
        dragmode="zoom",
        hovermode="x unified"
    )

    fig.update_xaxes(showspikes=True, spikemode="across", spikesnap="cursor", fixedrange=False)
    fig.update_yaxes(showspikes=False, fixedrange=True)

    return fig
