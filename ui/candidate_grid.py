import numpy as np
import plotly.graph_objects as go


def build_candidate_figure(
    values: np.ndarray,
    survives: np.ndarray,
    eliminated_by: np.ndarray,
    active_prime: int | None,
) -> go.Figure:
    """Create a precise tiled candidate field."""

    count = len(values)

    grid_width = max(
        10,
        int(np.ceil(np.sqrt(count))),
    )

    grid_height = int(
        np.ceil(count / grid_width)
    )

    total_cells = grid_width * grid_height

    status = np.full(
        total_cells,
        np.nan,
        dtype=float,
    )

    hover_text = np.full(
        total_cells,
        "",
        dtype=object,
    )

    status[:count] = 0

    survivor_indices = np.flatnonzero(
        survives
    )

    status[survivor_indices] = 1

    if active_prime is not None:
        current_mask = (
            eliminated_by == active_prime
        )

        current_indices = np.flatnonzero(
            current_mask
        )

        status[current_indices] = 2

    for index, value in enumerate(values):
        if survives[index]:
            state = "Surviving candidate"

        elif (
            active_prime is not None
            and eliminated_by[index] == active_prime
        ):
            state = (
                f"Removed by prime {active_prime}"
            )

        elif eliminated_by[index] > 0:
            state = (
                "Previously eliminated "
                f"by prime {eliminated_by[index]}"
            )

        else:
            state = "Not a prime candidate"

        hover_text[index] = (
            f"<b>{int(value):,}</b>"
            f"<br>{state}"
        )

    status_grid = status.reshape(
        grid_height,
        grid_width,
    )

    hover_grid = hover_text.reshape(
        grid_height,
        grid_width,
    )

    figure = go.Figure()

    figure.add_trace(
        go.Heatmap(
            z=status_grid,
            text=hover_grid,
            zmin=0,
            zmax=2,
            colorscale=[
                [0.000000, "#E3E8EF"],
                [0.333333, "#E3E8EF"],
                [0.333334, "#2457E6"],
                [0.666666, "#2457E6"],
                [0.666667, "#D97706"],
                [1.000000, "#D97706"],
            ],
            showscale=False,
            xgap=1,
            ygap=1,
            hoverongaps=False,
            hovertemplate=(
                "%{text}"
                "<extra></extra>"
            ),
        )
    )

    legend_entries = (
        (
            "Surviving candidate",
            "#2457E6",
        ),
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
                    "size": 11,
                    "color": color,
                    "symbol": "square",
                },
                name=name,
                hoverinfo="skip",
            )
        )

    figure.update_layout(
        height=650,
        margin={
            "l": 10,
            "r": 10,
            "t": 45,
            "b": 10,
        },
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "left",
            "x": 0,
            "itemclick": False,
            "itemdoubleclick": False,
        },
    )

    figure.update_xaxes(
        visible=False,
        fixedrange=True,
    )

    figure.update_yaxes(
        visible=False,
        fixedrange=True,
        autorange="reversed",
        scaleanchor="x",
        scaleratio=1,
    )

    return figure
