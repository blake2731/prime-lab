from collections.abc import Sequence

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from prime_lab.filter_efficiency import (
    filter_efficiency_steps,
)


def build_filter_efficiency_figure(
    start: int,
    end: int,
    filter_primes: Sequence[int],
) -> go.Figure:
    """Show each prime filter's unique eliminations and marginal yield."""

    steps = filter_efficiency_steps(
        start,
        end,
        filter_primes,
    )

    primes = [
        step.prime
        for step in steps
    ]

    removed = [
        step.removed
        for step in steps
    ]

    marginal_rates = [
        step.marginal_removal_rate * 100.0
        for step in steps
    ]

    survival_rates = [
        step.cumulative_survival_rate * 100.0
        for step in steps
    ]

    customdata = [
        [
            step.candidates_before,
            step.candidates_after,
            step.marginal_removal_rate * 100.0,
            step.cumulative_survival_rate * 100.0,
        ]
        for step in steps
    ]

    figure = make_subplots(
        specs=[[{"secondary_y": True}]],
    )

    figure.add_trace(
        go.Bar(
            x=primes,
            y=removed,
            customdata=customdata,
            name="Unique composites removed",
            marker={
                "color": "#D97706",
            },
            hovertemplate=(
                "<b>Prime %{x}</b>"
                "<br>Unique composites removed: %{y:,}"
                "<br>Candidates before: %{customdata[0]:,}"
                "<br>Candidates after: %{customdata[1]:,}"
                "<br>Marginal removal: %{customdata[2]:.2f}%"
                "<br>Cumulative survival: %{customdata[3]:.2f}%"
                "<extra></extra>"
            ),
        ),
        secondary_y=False,
    )

    figure.add_trace(
        go.Scatter(
            x=primes,
            y=marginal_rates,
            mode="lines+markers",
            name="Marginal removal rate",
            line={
                "color": "#2457E6",
                "width": 2.5,
            },
            marker={
                "size": 7,
            },
            hovertemplate=(
                "Prime %{x}"
                "<br>Marginal removal: %{y:.2f}%"
                "<extra></extra>"
            ),
        ),
        secondary_y=True,
    )

    figure.add_trace(
        go.Scatter(
            x=primes,
            y=survival_rates,
            mode="lines+markers",
            name="Candidates still surviving",
            line={
                "color": "#008A7C",
                "width": 2,
                "dash": "dot",
            },
            marker={
                "size": 6,
            },
            hovertemplate=(
                "Prime %{x}"
                "<br>Cumulative survival: %{y:.2f}%"
                "<extra></extra>"
            ),
        ),
        secondary_y=True,
    )

    figure.update_layout(
        height=470,
        margin={
            "l": 35,
            "r": 35,
            "t": 55,
            "b": 45,
        },
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.03,
            "xanchor": "left",
            "x": 0,
        },
        hovermode="x unified",
        bargap=0.28,
    )

    figure.update_xaxes(
        title_text="Prime filter",
        type="category",
        showgrid=False,
    )

    figure.update_yaxes(
        title_text="Unique composites removed",
        showgrid=True,
        gridcolor="#E3E8EF",
        rangemode="tozero",
        secondary_y=False,
    )

    figure.update_yaxes(
        title_text="Percent",
        ticksuffix="%",
        range=[0, 100],
        showgrid=False,
        secondary_y=True,
    )

    return figure
