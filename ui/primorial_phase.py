from math import cos, pi, sin

import plotly.graph_objects as go

from prime_lab.primorial_phase import (
    DensityConvergencePoint,
    PrimeDensityObservation,
    PrimorialStage,
)


CONFIRMED_PRIME = "#008A7C"
UNRESOLVED_CANDIDATE = "#2457E6"
NEWLY_RESOLVED = "#D97706"
RESOLVED_COMPOSITE = "#E3E8EF"
INK = "#172033"
MUTED = "#667085"


def build_survivor_fraction_figure(stages: tuple[PrimorialStage, ...]) -> go.Figure:
    """Compare exact primorial survivor fractions with the Mertens estimate."""

    if not stages:
        raise ValueError("at least one primorial stage is required")

    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=[stage.prime for stage in stages],
            y=[stage.survivor_fraction for stage in stages],
            mode="lines+markers",
            name="Exact survivor fraction",
            line={"color": UNRESOLVED_CANDIDATE, "width": 3},
            marker={"size": 8},
            customdata=[
                [stage.stage, stage.primorial, stage.surviving_states]
                for stage in stages
            ],
            hovertemplate=(
                "Activated through prime %{x}<br>"
                "Stage %{customdata[0]}<br>"
                "Primorial %{customdata[1]:,}<br>"
                "Surviving states %{customdata[2]:,}<br>"
                "Fraction %{y:.6f}<extra></extra>"
            ),
        )
    )
    figure.add_trace(
        go.Scatter(
            x=[stage.prime for stage in stages],
            y=[stage.mertens_estimate for stage in stages],
            mode="lines+markers",
            name="Mertens approximation",
            line={"color": CONFIRMED_PRIME, "width": 2, "dash": "dash"},
            marker={"size": 7},
            hovertemplate="Prime cutoff %{x}<br>e^(-γ) / ln(p) = %{y:.6f}<extra></extra>",
        )
    )
    figure.update_xaxes(title="Largest activated prime p")
    figure.update_yaxes(title="Fraction of joint residue states surviving", rangemode="tozero")
    figure.update_layout(
        height=460,
        margin={"l": 45, "r": 20, "t": 35, "b": 45},
        legend={"orientation": "h", "y": 1.1},
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    return figure


def build_primorial_wheel_figure(
    *,
    modulus: int,
    survivor_residues: tuple[int, ...],
    cutoff_prime: int,
) -> go.Figure:
    """Place one complete primorial residue period around a normalized circle."""

    if modulus < 2:
        raise ValueError("modulus must be at least 2")

    survivor_set = set(survivor_residues)
    eliminated_x: list[float] = []
    eliminated_y: list[float] = []
    surviving_x: list[float] = []
    surviving_y: list[float] = []
    surviving_labels: list[int] = []

    for residue in range(modulus):
        angle = 2 * pi * residue / modulus
        x = sin(angle)
        y = cos(angle)
        if residue in survivor_set:
            surviving_x.append(x)
            surviving_y.append(y)
            surviving_labels.append(residue)
        else:
            eliminated_x.append(x)
            eliminated_y.append(y)

    figure = go.Figure()
    figure.add_trace(
        go.Scattergl(
            x=eliminated_x,
            y=eliminated_y,
            mode="markers",
            name="Touches phase zero",
            marker={"size": 4, "color": RESOLVED_COMPOSITE, "opacity": 0.65},
            hoverinfo="skip",
        )
    )
    figure.add_trace(
        go.Scattergl(
            x=surviving_x,
            y=surviving_y,
            mode="markers",
            name="Avoids phase zero",
            marker={"size": 7, "color": UNRESOLVED_CANDIDATE, "opacity": 0.92},
            customdata=surviving_labels,
            hovertemplate="Surviving residue %{customdata}<extra></extra>",
        )
    )

    figure.add_annotation(
        x=0,
        y=0,
        text=(
            f"p ≤ {cutoff_prime}<br>"
            f"P = {modulus:,}<br>"
            f"{len(survivor_residues):,} survivors"
        ),
        showarrow=False,
        font={"size": 15, "color": INK},
        align="center",
    )

    figure.update_xaxes(visible=False, range=[-1.12, 1.12])
    figure.update_yaxes(visible=False, range=[-1.12, 1.12], scaleanchor="x", scaleratio=1)
    figure.update_layout(
        height=620,
        margin={"l": 10, "r": 10, "t": 35, "b": 10},
        legend={"orientation": "h", "y": 1.04},
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    return figure


def build_density_comparison_figure(observation: PrimeDensityObservation) -> go.Figure:
    """Compare periodic survivor density with finite observed prime density."""

    labels = [
        "Primorial survivor fraction",
        "Mertens at √x cutoff",
        "Observed π(x) / x",
        "Prime number theorem 1 / ln(x)",
    ]
    values = [
        observation.wheel_survivor_fraction,
        observation.mertens_at_proof_cutoff,
        observation.empirical_prime_density,
        observation.pnt_density,
    ]
    colors = [
        UNRESOLVED_CANDIDATE,
        CONFIRMED_PRIME,
        NEWLY_RESOLVED,
        MUTED,
    ]

    figure = go.Figure(
        go.Bar(
            x=labels,
            y=values,
            marker={"color": colors},
            text=[f"{value:.6f}" for value in values],
            textposition="outside",
            hovertemplate="%{x}<br>%{y:.8f}<extra></extra>",
        )
    )
    figure.update_yaxes(title="Density / fraction", rangemode="tozero")
    figure.update_layout(
        height=470,
        margin={"l": 45, "r": 20, "t": 30, "b": 110},
        plot_bgcolor="white",
        paper_bgcolor="white",
        showlegend=False,
    )
    return figure


def build_density_residual_figure(
    points: tuple[DensityConvergencePoint, ...],
) -> go.Figure:
    """Plot finite prime-density and primorial-density residuals across scale."""

    if not points:
        raise ValueError("at least one convergence point is required")

    x_values = [point.maximum_integer for point in points]
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=x_values,
            y=[point.prime_density_minus_pnt for point in points],
            mode="lines+markers",
            name="π(x)/x − 1/ln(x)",
            line={"color": NEWLY_RESOLVED, "width": 3},
            marker={"size": 8},
            hovertemplate="x = %{x:,}<br>prime-density residual = %{y:.8f}<extra></extra>",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=x_values,
            y=[point.wheel_minus_prime_density for point in points],
            mode="lines+markers",
            name="Primorial survivor − π(x)/x",
            line={"color": UNRESOLVED_CANDIDATE, "width": 3},
            marker={"size": 8},
            hovertemplate="x = %{x:,}<br>sieve-to-prime residual = %{y:.8f}<extra></extra>",
        )
    )
    figure.add_hline(y=0, line={"color": MUTED, "width": 1.5, "dash": "dot"})
    figure.update_xaxes(title="x", type="log", tickformat="~s")
    figure.update_yaxes(title="Signed density residual", zeroline=False)
    figure.update_layout(
        height=460,
        margin={"l": 55, "r": 20, "t": 35, "b": 45},
        legend={"orientation": "h", "y": 1.1},
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    return figure


def build_asymptotic_residual_figure(
    points: tuple[DensityConvergencePoint, ...],
) -> go.Figure:
    """Plot residuals against the Mertens and sqrt-cutoff asymptotic references."""

    if not points:
        raise ValueError("at least one convergence point is required")

    x_values = [point.maximum_integer for point in points]
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=x_values,
            y=[point.wheel_ratio_error for point in points],
            mode="lines+markers",
            name="Survivor/PNT ratio − 2e^(−γ)",
            line={"color": CONFIRMED_PRIME, "width": 3},
            marker={"size": 8},
            hovertemplate="x = %{x:,}<br>ratio residual = %{y:.8f}<extra></extra>",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=x_values,
            y=[point.mertens_absolute_error for point in points],
            mode="lines+markers",
            name="Exact survivor − Mertens estimate",
            line={"color": UNRESOLVED_CANDIDATE, "width": 2, "dash": "dash"},
            marker={"size": 7},
            hovertemplate="x = %{x:,}<br>Mertens residual = %{y:.8f}<extra></extra>",
        )
    )
    figure.add_hline(y=0, line={"color": MUTED, "width": 1.5, "dash": "dot"})
    figure.update_xaxes(title="x", type="log", tickformat="~s")
    figure.update_yaxes(title="Signed residual", zeroline=False)
    figure.update_layout(
        height=460,
        margin={"l": 55, "r": 20, "t": 35, "b": 45},
        legend={"orientation": "h", "y": 1.1},
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    return figure
