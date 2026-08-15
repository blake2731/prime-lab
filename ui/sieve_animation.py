from collections.abc import Sequence

import numpy as np
import plotly.graph_objects as go

from prime_lab.certification import certification_frontier, confirmed_prime_mask
from prime_lab.filters import filter_candidates
from ui.candidate_grid import (
    CONFIRMED_PRIME,
    INK,
    NEWLY_RESOLVED,
    RESOLVED_COMPOSITE,
    UNRESOLVED_CANDIDATE,
)


MUTED = "#667085"
VISIT_OUTLINE = "#2457E6"
BORDER = "#C7D0DD"
LABEL_LIMIT = 320


def _status_annotation(text: str) -> list[dict]:
    """Create the status label shown above the candidate field."""

    return [
        {
            "text": text,
            "xref": "paper",
            "yref": "paper",
            "x": 1,
            "y": 1.09,
            "xanchor": "right",
            "yanchor": "bottom",
            "showarrow": False,
            "font": {
                "size": 14,
                "color": MUTED,
                "family": "sans-serif",
            },
        }
    ]


def _slider_step(label: str, frame_name: str) -> dict:
    """Create one direct inspection step on the prime timeline."""

    return {
        "label": label,
        "method": "animate",
        "args": [
            [frame_name],
            {
                "frame": {"duration": 0, "redraw": False},
                "transition": {"duration": 0},
                "mode": "immediate",
            },
        ],
    }


def _grid_geometry(
    count: int,
    grid_width: int | None,
) -> tuple[np.ndarray, np.ndarray, int, int]:
    """Return fixed coordinates for every integer in the playback field."""

    if count < 1:
        raise ValueError("at least one value is required")

    if grid_width is None:
        resolved_width = max(8, int(np.ceil(np.sqrt(count))))
    else:
        if grid_width < 1:
            raise ValueError("grid_width must be at least 1")
        resolved_width = int(grid_width)

    resolved_height = int(np.ceil(count / resolved_width))
    indices = np.arange(count, dtype=int)
    x = indices % resolved_width
    y = indices // resolved_width
    return x, y, resolved_width, resolved_height


def _base_marker_size(count: int) -> float:
    """Keep small experiments tactile while bounding dense fields."""

    if count <= 120:
        return 30.0
    if count <= 320:
        return 23.0
    if count <= 700:
        return 17.0
    if count <= 1_100:
        return 13.0
    return 10.0


def _cascade_batch_count(event_count: int) -> int:
    """Choose enough stages to reveal periodic motion without dragging."""

    if event_count <= 1:
        return 1
    if event_count <= 10:
        return min(4, event_count)
    if event_count <= 30:
        return 5
    if event_count <= 80:
        return 7
    if event_count <= 180:
        return 8
    return 9


def _ordered_batches(indices: np.ndarray, batch_count: int) -> list[np.ndarray]:
    """Split an ordered prime path into consecutive visual beats."""

    if len(indices) == 0:
        return []

    return [
        batch.astype(int, copy=False)
        for batch in np.array_split(indices, min(batch_count, len(indices)))
        if len(batch)
    ]


def _state_colors(
    values: np.ndarray,
    survives: np.ndarray,
    confirmed: np.ndarray,
    active_elimination: np.ndarray,
) -> list[str]:
    """Map the exact sieve state onto the shared Prime Lab palette."""

    colors: list[str] = []
    for index, value in enumerate(values):
        if active_elimination[index]:
            colors.append(NEWLY_RESOLVED)
        elif confirmed[index]:
            colors.append(CONFIRMED_PRIME)
        elif survives[index] and value >= 2:
            colors.append(UNRESOLVED_CANDIDATE)
        else:
            colors.append(RESOLVED_COMPOSITE)
    return colors


def _text_colors(colors: Sequence[str]) -> list[str]:
    """Keep integer labels readable against categorical fills."""

    return [
        INK if color == RESOLVED_COMPOSITE else "#FFFFFF"
        for color in colors
    ]


def _hover_text(
    values: np.ndarray,
    survives: np.ndarray,
    eliminated_by: np.ndarray,
    confirmed: np.ndarray,
    active_prime: int | None,
    active_visit: np.ndarray,
    active_elimination: np.ndarray,
) -> list[str]:
    """Describe both state and the current mathematical action."""

    rows: list[str] = []
    for index, value in enumerate(values):
        if active_elimination[index] and active_prime is not None:
            description = (
                f"Prime {active_prime} reaches this surviving candidate now"
                "<br>and resolves it as composite."
            )
        elif active_visit[index] and active_prime is not None:
            owner = int(eliminated_by[index])
            if owner > 0:
                description = (
                    f"Prime {active_prime} visits this multiple now."
                    f"<br>It was already resolved by Prime {owner}."
                )
            else:
                description = f"Prime {active_prime} visits this multiple now."
        elif confirmed[index]:
            description = "Confirmed prime"
        elif survives[index] and value >= 2:
            description = "Unresolved candidate"
        elif eliminated_by[index] > 0:
            description = (
                "Resolved composite"
                f"<br>First eliminating prime: {int(eliminated_by[index])}"
            )
        else:
            description = "Not a prime candidate"

        rows.append(f"<b>{int(value):,}</b><br>{description}")
    return rows


def _playback_traces(
    *,
    values: np.ndarray,
    x: np.ndarray,
    y: np.ndarray,
    survives: np.ndarray,
    eliminated_by: np.ndarray,
    confirmed: np.ndarray,
    active_prime: int | None,
    active_visit: np.ndarray,
    active_elimination: np.ndarray,
    focus_color: str,
    marker_size: float,
    show_labels: bool,
) -> tuple[go.Scatter, go.Scatter]:
    """Build the persistent field trace and its transient focus pulse."""

    colors = _state_colors(
        values,
        survives,
        confirmed,
        active_elimination,
    )
    labels = [str(int(value)) if show_labels else "" for value in values]
    text_colors = _text_colors(colors)
    hover = _hover_text(
        values,
        survives,
        eliminated_by,
        confirmed,
        active_prime,
        active_visit,
        active_elimination,
    )

    main = go.Scatter(
        x=x,
        y=y,
        mode="markers+text" if show_labels else "markers",
        text=labels,
        customdata=hover,
        textposition="middle center",
        textfont={
            "family": "monospace",
            "size": max(8, int(marker_size * 0.43)),
            "color": text_colors,
        },
        marker={
            "symbol": "square",
            "size": marker_size,
            "color": colors,
            "line": {"width": 1, "color": BORDER},
        },
        hovertemplate="%{customdata}<extra></extra>",
        showlegend=False,
    )

    focus_sizes = [
        marker_size * 1.42 if active_visit[index] else 0.1
        for index in range(len(values))
    ]
    focus = go.Scatter(
        x=x,
        y=y,
        mode="markers",
        marker={
            "symbol": "square-open",
            "size": focus_sizes,
            "color": focus_color,
            "line": {"width": 2.4, "color": focus_color},
        },
        hoverinfo="skip",
        showlegend=False,
    )
    return main, focus


def _animation_frame(
    name: str,
    main: go.Scatter,
    focus: go.Scatter,
    status: str,
) -> go.Frame:
    """Create one fixed-layout scatter frame for smooth browser playback."""

    return go.Frame(
        name=name,
        data=[main, focus],
        traces=[0, 1],
        layout=go.Layout(annotations=_status_annotation(status)),
    )


def _legend_trace(name: str, color: str, *, open_marker: bool = False) -> go.Scatter:
    """Create a noninteractive legend swatch."""

    return go.Scatter(
        x=[None],
        y=[None],
        mode="markers",
        marker={
            "size": 11,
            "symbol": "square-open" if open_marker else "square",
            "color": color,
            "line": {"width": 2 if open_marker else 0, "color": color},
        },
        name=name,
        hoverinfo="skip",
    )


def build_sieve_animation(
    start: int,
    end: int,
    filter_primes: Sequence[int],
    grid_width: int | None = None,
) -> go.Figure:
    """Build a staged, mathematically faithful sieve cascade.

    Every integer stays anchored to a fixed position for the entire animation.
    Each prime first receives focus, then advances through its actual multiples
    in ascending order. A multiple that is still a candidate turns amber at
    the moment that prime first resolves it; an already resolved multiple
    receives only the outline pulse. After the divisibility sweep completes,
    newly certified primes are revealed in a separate proof-frontier stage.

    The static Prime Lab field remains the analytical companion to this replay.
    A reduced-motion playback path skips all transient pulses and visits only
    the settled filter checkpoints.
    """

    primes = tuple(filter_primes)
    values, start_survives, start_eliminated_by = filter_candidates(start, end, ())
    count = len(values)
    x, y, resolved_width, resolved_height = _grid_geometry(count, grid_width)
    marker_size = _base_marker_size(count)
    show_labels = count <= LABEL_LIMIT
    no_focus = np.zeros(values.shape, dtype=bool)
    start_confirmed = np.zeros(values.shape, dtype=bool)

    start_main, start_focus = _playback_traces(
        values=values,
        x=x,
        y=y,
        survives=start_survives,
        eliminated_by=start_eliminated_by,
        confirmed=start_confirmed,
        active_prime=None,
        active_visit=no_focus,
        active_elimination=no_focus,
        focus_color=VISIT_OUTLINE,
        marker_size=marker_size,
        show_labels=show_labels,
    )

    start_candidates = int(np.count_nonzero(values >= 2))
    figure = go.Figure(
        data=[
            start_main,
            start_focus,
            _legend_trace("Unresolved candidate", UNRESOLVED_CANDIDATE),
            _legend_trace("Confirmed prime", CONFIRMED_PRIME),
            _legend_trace("Newly resolved composite", NEWLY_RESOLVED),
            _legend_trace("Resolved composite", RESOLVED_COMPOSITE),
            _legend_trace("Active prime path", VISIT_OUTLINE, open_marker=True),
        ]
    )

    chart_height = min(820, max(480, 165 + resolved_height * 31))
    figure.update_layout(
        height=chart_height,
        margin={"l": 10, "r": 10, "t": 75, "b": 135},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        annotations=_status_annotation(
            f"Start  |  {start_candidates:,} prime candidates  |  no filters applied"
        ),
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "left",
            "x": 0,
            "itemclick": False,
            "itemdoubleclick": False,
        },
        hoverlabel={"font": {"family": "sans-serif"}},
    )
    figure.update_xaxes(
        range=[-0.7, resolved_width - 0.3],
        visible=False,
        fixedrange=True,
        autorange=False,
    )
    figure.update_yaxes(
        range=[resolved_height - 0.3, -0.7],
        visible=False,
        fixedrange=True,
        autorange=False,
        scaleanchor="x",
        scaleratio=1,
    )

    frames: list[go.Frame] = [
        _animation_frame(
            "start",
            start_main,
            start_focus,
            f"Start  |  {start_candidates:,} prime candidates  |  no filters applied",
        )
    ]
    full_playback_names = ["start"]
    reduced_playback_names = ["start"]
    slider_steps = [_slider_step("Start", "start")]

    if not primes:
        figure.frames = frames
        return figure

    previous_survives = start_survives.copy()
    previous_eliminated_by = start_eliminated_by.copy()
    previous_confirmed = start_confirmed.copy()

    for step, prime in enumerate(primes):
        stage_primes = primes[: step + 1]
        stage_values, stage_survives, stage_eliminated_by = filter_candidates(
            start,
            end,
            stage_primes,
        )
        stage_confirmed = confirmed_prime_mask(
            stage_values,
            stage_survives,
            stage_primes,
        )
        frontier = certification_frontier(stage_primes)

        newly_eliminated = previous_survives & ~stage_survives
        newly_confirmed = stage_confirmed & ~previous_confirmed

        prime_focus = stage_values == prime
        focus_main, focus_trace = _playback_traces(
            values=stage_values,
            x=x,
            y=y,
            survives=previous_survives,
            eliminated_by=previous_eliminated_by,
            confirmed=previous_confirmed,
            active_prime=prime,
            active_visit=prime_focus,
            active_elimination=no_focus,
            focus_color=VISIT_OUTLINE,
            marker_size=marker_size,
            show_labels=show_labels,
        )
        focus_name = f"prime_{prime}_focus"
        frames.append(
            _animation_frame(
                focus_name,
                focus_main,
                focus_trace,
                f"Prime {prime} enters  |  following multiples spaced every {prime} integers",
            )
        )
        full_playback_names.append(focus_name)

        visit_indices = np.flatnonzero(
            (stage_values >= 2)
            & (stage_values != prime)
            & (stage_values % prime == 0)
        )
        batches = _ordered_batches(
            visit_indices,
            _cascade_batch_count(len(visit_indices)),
        )

        progressive_survives = previous_survives.copy()
        progressive_eliminated_by = previous_eliminated_by.copy()
        resolved_by_prime = 0

        for batch_number, batch in enumerate(batches, start=1):
            active_visit = np.zeros(stage_values.shape, dtype=bool)
            active_visit[batch] = True
            active_elimination = active_visit & newly_eliminated

            progressive_survives[active_elimination] = False
            progressive_eliminated_by[active_elimination] = prime
            resolved_by_prime += int(np.count_nonzero(active_elimination))

            batch_main, batch_focus = _playback_traces(
                values=stage_values,
                x=x,
                y=y,
                survives=progressive_survives,
                eliminated_by=progressive_eliminated_by,
                confirmed=previous_confirmed,
                active_prime=prime,
                active_visit=active_visit,
                active_elimination=active_elimination,
                focus_color=VISIT_OUTLINE,
                marker_size=marker_size,
                show_labels=show_labels,
            )

            first_value = int(stage_values[int(batch[0])])
            last_value = int(stage_values[int(batch[-1])])
            cascade_name = f"prime_{prime}_cascade_{batch_number}"
            frames.append(
                _animation_frame(
                    cascade_name,
                    batch_main,
                    batch_focus,
                    f"Prime {prime} sweeps its multiples  |  "
                    f"{first_value:,} to {last_value:,}  |  "
                    f"{resolved_by_prime:,}/{int(np.count_nonzero(newly_eliminated)):,} new composites resolved",
                )
            )
            full_playback_names.append(cascade_name)

        certification_indices = np.flatnonzero(newly_confirmed)
        certification_batches = _ordered_batches(
            certification_indices,
            min(4, max(1, len(certification_indices))),
        )
        progressive_confirmed = previous_confirmed.copy()

        for batch_number, batch in enumerate(certification_batches, start=1):
            certification_focus = np.zeros(stage_values.shape, dtype=bool)
            certification_focus[batch] = True
            progressive_confirmed[batch] = True

            cert_main, cert_focus = _playback_traces(
                values=stage_values,
                x=x,
                y=y,
                survives=stage_survives,
                eliminated_by=stage_eliminated_by,
                confirmed=progressive_confirmed,
                active_prime=prime,
                active_visit=certification_focus,
                active_elimination=no_focus,
                focus_color=CONFIRMED_PRIME,
                marker_size=marker_size,
                show_labels=show_labels,
            )
            certification_name = f"prime_{prime}_certify_{batch_number}"
            frames.append(
                _animation_frame(
                    certification_name,
                    cert_main,
                    cert_focus,
                    f"Proof frontier expands to n < {frontier:,}  |  "
                    f"{int(np.count_nonzero(progressive_confirmed & ~previous_confirmed)):,}/"
                    f"{int(np.count_nonzero(newly_confirmed)):,} newly confirmed primes revealed",
                )
            )
            full_playback_names.append(certification_name)

        settled_main, settled_focus = _playback_traces(
            values=stage_values,
            x=x,
            y=y,
            survives=stage_survives,
            eliminated_by=stage_eliminated_by,
            confirmed=stage_confirmed,
            active_prime=prime,
            active_visit=no_focus,
            active_elimination=no_focus,
            focus_color=VISIT_OUTLINE,
            marker_size=marker_size,
            show_labels=show_labels,
        )
        settle_name = f"prime_{prime}_settle"
        frames.append(
            _animation_frame(
                settle_name,
                settled_main,
                settled_focus,
                f"Prime {prime} complete  |  "
                f"{int(np.count_nonzero(stage_survives & (stage_values >= 2))):,} candidates remain  |  "
                f"{int(np.count_nonzero(stage_confirmed)):,} confirmed primes  |  "
                f"proof frontier n < {frontier:,}",
            )
        )
        full_playback_names.append(settle_name)
        reduced_playback_names.append(settle_name)
        slider_steps.append(_slider_step(str(prime), settle_name))

        previous_survives = stage_survives.copy()
        previous_eliminated_by = stage_eliminated_by.copy()
        previous_confirmed = stage_confirmed.copy()

    figure.frames = frames
    figure.update_layout(
        updatemenus=[
            {
                "type": "buttons",
                "direction": "left",
                "showactive": False,
                "x": 0,
                "y": 0,
                "xanchor": "left",
                "yanchor": "top",
                "pad": {"t": 58, "r": 10},
                "buttons": [
                    {
                        "label": "▶ Play cascade",
                        "method": "animate",
                        "args": [
                            full_playback_names,
                            {
                                "frame": {"duration": 180, "redraw": False},
                                "transition": {
                                    "duration": 110,
                                    "easing": "cubic-in-out",
                                },
                                "fromcurrent": False,
                                "mode": "immediate",
                            },
                        ],
                    },
                    {
                        "label": "❚❚ Pause",
                        "method": "animate",
                        "args": [
                            [None],
                            {
                                "frame": {"duration": 0, "redraw": False},
                                "transition": {"duration": 0},
                                "mode": "immediate",
                            },
                        ],
                    },
                    {
                        "label": "◫ Reduced motion",
                        "method": "animate",
                        "args": [
                            reduced_playback_names,
                            {
                                "frame": {"duration": 520, "redraw": False},
                                "transition": {"duration": 0},
                                "fromcurrent": False,
                                "mode": "immediate",
                            },
                        ],
                    },
                    {
                        "label": "↺ Start",
                        "method": "animate",
                        "args": [
                            ["start"],
                            {
                                "frame": {"duration": 0, "redraw": False},
                                "transition": {"duration": 0},
                                "mode": "immediate",
                            },
                        ],
                    },
                ],
            }
        ],
        sliders=[
            {
                "active": 0,
                "x": 0.28,
                "y": 0,
                "len": 0.72,
                "xanchor": "left",
                "yanchor": "top",
                "pad": {"t": 52},
                "currentvalue": {
                    "prefix": "Settled filter stage: ",
                    "visible": True,
                    "xanchor": "right",
                },
                "steps": slider_steps,
            }
        ],
    )

    return figure
