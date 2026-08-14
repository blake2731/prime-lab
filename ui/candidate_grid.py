import numpy as np
import plotly.graph_objects as go


RESOLVED_COMPOSITE = "#E3E8EF"
UNRESOLVED_CANDIDATE = "#2457E6"
NEWLY_RESOLVED = "#D97706"
CONFIRMED_PRIME = "#008A7C"
INK = "#172033"
LABEL_LIMIT = 400


def build_candidate_figure(
    values: np.ndarray,
    survives: np.ndarray,
    eliminated_by: np.ndarray,
    active_prime: int | None,
    confirmed: np.ndarray | None = None,
    current_elimination: np.ndarray | None = None,
    grid_width: int | None = None,
) -> go.Figure:
    """Create a tiled view of one exact candidate state.

    Small fields display integer labels directly. Larger fields preserve the
    same state encoding but rely on hover inspection so the chart remains
    legible and responsive.
    """

    count = len(values)
    if count == 0:
        raise ValueError("at least one value is required")

    if grid_width is None:
        resolved_grid_width = max(
            8,
            int(np.ceil(np.sqrt(count))),
        )
    else:
        if grid_width < 1:
            raise ValueError("grid_width must be at least 1")
        resolved_grid_width = int(grid_width)

    grid_height = int(np.ceil(count / resolved_grid_width))
    total_cells = resolved_grid_width * grid_height

    status = np.full(total_cells, np.nan, dtype=float)
    hover_text = np.full(total_cells, "", dtype=object)
    status[:count] = 0

    survivor_indices = np.flatnonzero(survives)
    status[survivor_indices] = 1

    if confirmed is not None:
        confirmed_indices = np.flatnonzero(confirmed)
        status[confirmed_indices] = 3

    if current_elimination is not None:
        current_mask = np.asarray(current_elimination, dtype=bool)
    elif active_prime is not None:
        current_mask = eliminated_by == active_prime
    else:
        current_mask = np.zeros(values.shape, dtype=bool)

    current_indices = np.flatnonzero(current_mask)
    status[current_indices] = 2

    for index, value in enumerate(values):
        if confirmed is not None and confirmed[index]:
            state = "Confirmed prime"
        elif survives[index]:
            state = "Unresolved candidate"
        elif current_mask[index]:
            state = (
                f"First eliminated by prime {active_prime}"
                if active_prime is not None
                else "Newly resolved composite"
            )
        elif eliminated_by[index] > 0:
            state = f"Resolved composite · first eliminated by prime {eliminated_by[index]}"
        else:
            state = "Not a prime candidate"

        hover_text[index] = f"<b>{int(value):,}</b><br>{state}"

    status_grid = status.reshape(grid_height, resolved_grid_width)
    hover_grid = hover_text.reshape(grid_height, resolved_grid_width)

    figure = go.Figure()
    figure.add_trace(
        go.Heatmap(
            z=status_grid,
            text=hover_grid,
            zmin=0,
            zmax=3,
            colorscale=[
                [0.000000, RESOLVED_COMPOSITE],
                [0.166666, RESOLVED_COMPOSITE],
                [0.166667, UNRESOLVED_CANDIDATE],
                [0.499999, UNRESOLVED_CANDIDATE],
                [0.500000, NEWLY_RESOLVED],
                [0.833332, NEWLY_RESOLVED],
                [0.833333, CONFIRMED_PRIME],
                [1.000000, CONFIRMED_PRIME],
            ],
            showscale=False,
            xgap=1,
            ygap=1,
            hoverongaps=False,
            hovertemplate="%{text}<extra></extra>",
        )
    )

    if count <= LABEL_LIMIT:
        label_x: list[int] = []
        label_y: list[int] = []
        label_text: list[str] = []
        label_color: list[str] = []

        for index, value in enumerate(values):
            row = index // resolved_grid_width
            column = index % resolved_grid_width
            label_x.append(column)
            label_y.append(row)
            label_text.append(str(int(value)))

            state_code = status[index]
            label_color.append(
                INK if state_code == 0 else "#FFFFFF"
            )

        font_size = 12 if count <= 160 else 10
        figure.add_trace(
            go.Scatter(
                x=label_x,
                y=label_y,
                mode="text",
                text=label_text,
                textfont={"size": font_size, "color": label_color},
                hoverinfo="skip",
                showlegend=False,
            )
        )

    legend_entries = (
        ("Unresolved candidate", UNRESOLVED_CANDIDATE),
        ("Confirmed prime", CONFIRMED_PRIME),
        ("Resolved composite", RESOLVED_COMPOSITE),
        ("First eliminated by current filter", NEWLY_RESOLVED),
    )

    for name, color in legend_entries:
        figure.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode="markers",
                marker={"size": 11, "color": color, "symbol": "square"},
                name=name,
                hoverinfo="skip",
            )
        )

    chart_height = min(780, max(380, 110 + grid_height * 30))
    figure.update_layout(
        height=chart_height,
        margin={"l": 10, "r": 10, "t": 45, "b": 10},
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

    figure.update_xaxes(visible=False, fixedrange=True)
    figure.update_yaxes(
        visible=False,
        fixedrange=True,
        autorange="reversed",
        scaleanchor="x",
        scaleratio=1,
    )

    return figure
