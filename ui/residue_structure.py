from math import gcd

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


MODULUS = 30
PRIME_ELIGIBLE_RESIDUES = tuple(
    residue
    for residue in range(MODULUS)
    if gcd(residue, MODULUS) == 1
)


def _current_elimination_mask(
    values: np.ndarray,
    eliminated_by: np.ndarray,
    active_prime: int | None,
    current_elimination: np.ndarray | None,
) -> np.ndarray:
    """Resolve which cells belong to the current elimination event."""

    if current_elimination is not None:
        mask = np.asarray(
            current_elimination,
            dtype=bool,
        )

        if mask.shape != values.shape:
            raise ValueError(
                "current_elimination must match values shape"
            )

        return mask

    if active_prime is None:
        return np.zeros(
            values.shape,
            dtype=bool,
        )

    return eliminated_by == active_prime


def _state_name(
    index: int,
    survives: np.ndarray,
    eliminated_by: np.ndarray,
    confirmed: np.ndarray,
    active_prime: int | None,
    current_mask: np.ndarray,
) -> str:
    """Describe the mathematical state of one value."""

    if confirmed[index]:
        return "Confirmed prime"

    if survives[index]:
        return "Surviving candidate"

    if current_mask[index]:
        if active_prime is None:
            return "Currently eliminated"

        return f"Removed by prime {active_prime}"

    if eliminated_by[index] > 0:
        return (
            "Previously eliminated "
            f"by prime {eliminated_by[index]}"
        )

    return "Not a prime candidate"


def build_residue_figure(
    values: np.ndarray,
    survives: np.ndarray,
    eliminated_by: np.ndarray,
    confirmed: np.ndarray,
    active_prime: int | None,
    modulus: int = MODULUS,
    current_elimination: np.ndarray | None = None,
) -> go.Figure:
    """Arrange candidate states by residue class modulo a wheel modulus."""

    if modulus < 2:
        raise ValueError("modulus must be at least 2")

    current_mask = _current_elimination_mask(
        values,
        eliminated_by,
        active_prime,
        current_elimination,
    )

    quotients = values // modulus
    residues = values % modulus

    minimum_quotient = int(np.min(quotients))
    maximum_quotient = int(np.max(quotients))

    column_count = (
        maximum_quotient
        - minimum_quotient
        + 1
    )

    status = np.full(
        (modulus, column_count),
        np.nan,
        dtype=float,
    )

    hover_text = np.full(
        (modulus, column_count),
        "",
        dtype=object,
    )

    for index, value in enumerate(values):
        residue = int(residues[index])
        column = int(
            quotients[index]
            - minimum_quotient
        )

        if confirmed[index]:
            state_code = 3

        elif survives[index]:
            state_code = 1

        elif current_mask[index]:
            state_code = 2

        else:
            state_code = 0

        status[residue, column] = state_code

        state = _state_name(
            index,
            survives,
            eliminated_by,
            confirmed,
            active_prime,
            current_mask,
        )

        hover_text[residue, column] = (
            f"<b>{int(value):,}</b>"
            f"<br>{int(value):,} = "
            f"{modulus} × {int(quotients[index]):,} "
            f"+ {residue}"
            f"<br>Residue {residue} mod {modulus}"
            f"<br>{state}"
        )

    unresolved_counts = np.zeros(
        modulus,
        dtype=int,
    )

    confirmed_counts = np.zeros(
        modulus,
        dtype=int,
    )

    for residue in range(modulus):
        residue_mask = residues == residue

        unresolved_counts[residue] = int(
            np.count_nonzero(
                residue_mask
                & survives
                & ~confirmed
            )
        )

        confirmed_counts[residue] = int(
            np.count_nonzero(
                residue_mask
                & confirmed
            )
        )

    figure = make_subplots(
        rows=1,
        cols=2,
        shared_yaxes=True,
        column_widths=[0.84, 0.16],
        horizontal_spacing=0.035,
    )

    figure.add_trace(
        go.Heatmap(
            z=status,
            text=hover_text,
            zmin=0,
            zmax=3,
            colorscale=[
                [0.000000, "#E3E8EF"],
                [0.166666, "#E3E8EF"],
                [0.166667, "#2457E6"],
                [0.499999, "#2457E6"],
                [0.500000, "#D97706"],
                [0.833332, "#D97706"],
                [0.833333, "#008A7C"],
                [1.000000, "#008A7C"],
            ],
            showscale=False,
            xgap=1,
            ygap=1,
            hoverongaps=False,
            hovertemplate=(
                "%{text}"
                "<extra></extra>"
            ),
        ),
        row=1,
        col=1,
    )

    figure.add_trace(
        go.Bar(
            x=unresolved_counts,
            y=np.arange(modulus),
            orientation="h",
            marker={
                "color": "#2457E6",
            },
            name="Surviving candidate",
            hovertemplate=(
                "Residue %{y}"
                "<br>Unresolved %{x:,}"
                "<extra></extra>"
            ),
        ),
        row=1,
        col=2,
    )

    figure.add_trace(
        go.Bar(
            x=confirmed_counts,
            y=np.arange(modulus),
            orientation="h",
            marker={
                "color": "#008A7C",
            },
            name="Confirmed prime",
            hovertemplate=(
                "Residue %{y}"
                "<br>Confirmed %{x:,}"
                "<extra></extra>"
            ),
        ),
        row=1,
        col=2,
    )

    legend_entries = (
        (
            "Previously eliminated",
            "#E3E8EF",
        ),
        (
            "Removed by current filter",
            "#D97706",
        ),
    )

    for name, color in legend_entries:
        figure.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode="markers",
                marker={
                    "size": 10,
                    "color": color,
                    "symbol": "square",
                },
                name=name,
                hoverinfo="skip",
            ),
            row=1,
            col=1,
        )

    if modulus == MODULUS:
        eligible_text = "  ".join(
            str(residue)
            for residue in PRIME_ELIGIBLE_RESIDUES
        )

        figure.add_annotation(
            xref="paper",
            yref="paper",
            x=0,
            y=1.12,
            xanchor="left",
            yanchor="bottom",
            showarrow=False,
            text=(
                "<b>Modulo 30 structure</b>  ·  "
                "prime eligible residues above 5: "
                f"{eligible_text}"
            ),
            font={
                "size": 14,
                "color": "#172033",
            },
        )

    figure.add_annotation(
        xref="paper",
        yref="paper",
        x=1,
        y=1.12,
        xanchor="right",
        yanchor="bottom",
        showarrow=False,
        text="Survivors by residue",
        font={
            "size": 13,
            "color": "#566173",
        },
    )

    figure.update_layout(
        height=690,
        barmode="stack",
        margin={
            "l": 55,
            "r": 20,
            "t": 90,
            "b": 55,
        },
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.03,
            "xanchor": "left",
            "x": 0,
            "itemclick": False,
            "itemdoubleclick": False,
        },
    )

    figure.update_xaxes(
        title_text=(
            f"Quotient k in n = {modulus}k + r"
        ),
        showgrid=False,
        zeroline=False,
        row=1,
        col=1,
    )

    figure.update_xaxes(
        title_text="survivors",
        showgrid=True,
        gridcolor="#E3E8EF",
        zeroline=False,
        row=1,
        col=2,
    )

    figure.update_yaxes(
        title_text=f"Residue r mod {modulus}",
        tickmode="linear",
        tick0=0,
        dtick=1,
        range=[modulus - 0.5, -0.5],
        fixedrange=True,
        row=1,
        col=1,
    )

    return figure
