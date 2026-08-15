from collections.abc import Sequence

import numpy as np
import plotly.graph_objects as go

from prime_lab.certification import certification_frontier, confirmed_prime_mask
from prime_lab.filters import filter_candidates
from ui.candidate_grid import build_candidate_figure


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
                "color": "#566173",
                "family": "sans-serif",
            },
        }
    ]


def _animation_frame(name: str, figure: go.Figure, status: str) -> go.Frame:
    """Create one exact playback frame."""

    return go.Frame(
        name=name,
        data=list(figure.data),
        traces=list(range(len(figure.data))),
        layout=go.Layout(annotations=_status_annotation(status)),
    )


def _slider_step(label: str, frame_name: str) -> dict:
    """Create one direct inspection step on the prime timeline."""

    return {
        "label": label,
        "method": "animate",
        "args": [
            [frame_name],
            {
                "frame": {"duration": 0, "redraw": True},
                "transition": {"duration": 0},
                "mode": "immediate",
            },
        ],
    }


def build_sieve_animation(
    start: int,
    end: int,
    filter_primes: Sequence[int],
    grid_width: int | None = None,
) -> go.Figure:
    """Build filter by filter playback of one exact sieve experiment.

    Each prime stage has two states. The impact state highlights every
    candidate first resolved by that prime in amber. The settle state turns
    those composites gray while retaining any newly certified primes in teal.
    The sequence therefore replays the exact committed sieve without the old
    scattered rainfall effect.
    """

    primes = tuple(filter_primes)
    values, start_survives, start_eliminated_by = filter_candidates(
        start,
        end,
        (),
    )
    start_confirmed = np.zeros(values.shape, dtype=bool)

    figure = build_candidate_figure(
        values,
        start_survives,
        start_eliminated_by,
        None,
        start_confirmed,
        current_elimination=np.zeros(values.shape, dtype=bool),
        grid_width=grid_width,
    )

    start_candidates = int(np.count_nonzero(values >= 2))
    figure.update_layout(
        height=max(520, figure.layout.height or 520),
        margin={"l": 10, "r": 10, "t": 70, "b": 125},
        annotations=_status_annotation(
            f"Start  |  {start_candidates:,} prime candidates  |  no filters applied"
        ),
    )

    frames: list[go.Frame] = [
        _animation_frame(
            "start",
            figure,
            f"Start  |  {start_candidates:,} prime candidates  |  no filters applied",
        )
    ]
    playback_names = ["start"]
    slider_steps = [_slider_step("Start", "start")]

    if not primes:
        figure.frames = frames
        return figure

    previous_survives = start_survives
    previous_eliminated_by = start_eliminated_by
    previous_confirmed = start_confirmed

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

        impact_figure = build_candidate_figure(
            stage_values,
            stage_survives,
            stage_eliminated_by,
            prime,
            stage_confirmed,
            current_elimination=newly_eliminated,
            grid_width=grid_width,
        )
        impact_name = f"prime_{prime}_impact"
        frames.append(
            _animation_frame(
                impact_name,
                impact_figure,
                f"Prime {prime} acts  |  "
                f"{int(np.count_nonzero(newly_eliminated)):,} newly resolved composites  |  "
                f"{int(np.count_nonzero(newly_confirmed)):,} newly certified primes  |  "
                f"proof frontier n < {frontier:,}",
            )
        )
        playback_names.append(impact_name)

        settled_figure = build_candidate_figure(
            stage_values,
            stage_survives,
            stage_eliminated_by,
            prime,
            stage_confirmed,
            current_elimination=np.zeros(stage_values.shape, dtype=bool),
            grid_width=grid_width,
        )
        settle_name = f"prime_{prime}_settle"
        frames.append(
            _animation_frame(
                settle_name,
                settled_figure,
                f"Prime {prime} complete  |  "
                f"{int(np.count_nonzero(stage_survives & (stage_values >= 2))):,} candidates remain  |  "
                f"{int(np.count_nonzero(stage_confirmed)):,} confirmed primes  |  "
                f"proof frontier n < {frontier:,}",
            )
        )
        playback_names.append(settle_name)
        slider_steps.append(_slider_step(str(prime), settle_name))

        previous_survives = stage_survives
        previous_eliminated_by = stage_eliminated_by
        previous_confirmed = stage_confirmed

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
                "pad": {"t": 55, "r": 10},
                "buttons": [
                    {
                        "label": "▶ Play sieve",
                        "method": "animate",
                        "args": [
                            playback_names,
                            {
                                "frame": {"duration": 650, "redraw": True},
                                "transition": {"duration": 120},
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
                                "frame": {"duration": 0, "redraw": True},
                                "transition": {"duration": 0},
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
                                "frame": {"duration": 0, "redraw": True},
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
                "x": 0.25,
                "y": 0,
                "len": 0.75,
                "xanchor": "left",
                "yanchor": "top",
                "pad": {"t": 48},
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
