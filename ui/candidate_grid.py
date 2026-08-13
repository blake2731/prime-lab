import numpy as np
import plotly.graph_objects as go


def build_candidate_figure(
    values: np.ndarray,
    survives: np.ndarray,
    eliminated_by: np.ndarray,
    active_prime: int | None,
    confirmed: np.ndarray | None = None,
    active_elimination_mask: np.ndarray | None = None,
    scan_mask: np.ndarray | None = None,
    include_hover: bool = True,
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

    if active_elimination_mask is not None:
        current_mask = active_elimination_mask

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

    if scan_mask is not None:
        scan_indices = np.flatnonzero(
            scan_mask
        )

        status[scan_indices] = 4

    hover_text = None

    if include_hover:
        hover_text = np.full(
            total_cells,
            "",
            dtype=object,
        )

        for index, value in enumerate(values):
            if (
                scan_mask is not None
                and scan_mask[index]
            ):
                if active_prime is None:
                    state = "Current scan"
                else:
                    state = (
                        f"Testing with prime {active_prime}"
                    )

            elif current_mask[index]:
                state = (
                    f"Removed by prime {active_prime}"
                )

            elif (
                confirmed is not None
                and confirmed[index]
            ):
                state = "Confirmed prime"

            elif survives[index]:
                state = "Surviving candidate"

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

    if hover_text is None:
        hover_grid = None
    else:
        hover_grid = hover_text.reshape(
            grid_height,
            grid_width,
        )

    figure = go.Figure()

    heatmap_kwargs = {
        "z": status_grid,
        "zmin": 0,
        "zmax": 4,
        "colorscale": [
            [0.000000, "#E3E8EF"],
            [0.124999, "#E3E8EF"],
            [0.125000, "#2457E6"],
            [0.374999, "#2457E6"],
            [0.375000, "#D97706"],
            [0.624999, "#D97706"],
            [0.625000, "#008A7C"],
            [0.874999, "#008A7C"],
            [0.875000, "#F3C969"],
            [1.000000, "#F3C969"],
        ],
        "showscale": False,
        "xgap": 1,
        "ygap": 1,
        "hoverongaps": False,
    }

    if include_hover:
        heatmap_kwargs["text"] = hover_grid
        heatmap_kwargs["hovertemplate"] = (
            "%{text}<extra></extra>"
        )
    else:
        heatmap_kwargs["hoverinfo"] = "skip"

    figure.add_trace(
        go.Heatmap(
            **heatmap_kwargs
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
        (
            "Current scan",
            "#F3C969",
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
