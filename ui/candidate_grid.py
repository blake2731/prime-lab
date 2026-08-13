import numpy as np
import plotly.graph_objects as go


def build_candidate_figure(
    values: np.ndarray,
    survives: np.ndarray,
    eliminated_by: np.ndarray,
    active_prime: int | None,
    confirmed: np.ndarray | None = None,
    current_elimination: np.ndarray | None = None,
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

    if confirmed is not None:
        confirmed_indices = np.flatnonzero(
            confirmed
        )

        status[confirmed_indices] = 3

    if current_elimination is not None:
        current_mask = np.asarray(
            current_elimination,
            dtype=bool,
        )

    elif active_prime is not None:
        current_mask = (
            eliminated_by == active_prime
        )

    else:
        current_mask = np.zeros(
            values.shape,
            dtype=bool,
        )

    current_indices = np.flatnonzero(
        current_mask
    )

    status[current_indices] = 2

    for index, value in enumerate(values):
        if (
            confirmed is not None
            and confirmed[index]
        ):
            state = "Confirmed prime"

        elif survives[index]:
            state = "Surviving candidate"

        elif current_mask[index]:
            state = (
                f"Removed by prime {active_prime}"
                if active_prime is not None
                else "Currently eliminated"
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
        )
    )

    legend_entries = (
        (
            "Surviving candidate",
            "#2457E6",
        ),
        (
            "Confirmed prime",
            "#008A7C",
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
