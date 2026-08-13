from collections.abc import Sequence

import numpy as np
import plotly.graph_objects as go

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
            },
        }
    ]


def build_sieve_animation(
    start: int,
    end: int,
    filter_primes: Sequence[int],
) -> go.Figure:
    """Build one browser controlled animation of the sieve sequence."""

    primes = tuple(filter_primes)

    if not primes:
        values, survives, eliminated_by = filter_candidates(
            start,
            end,
            (),
        )

        return build_candidate_figure(
            values,
            survives,
            eliminated_by,
            None,
        )

    final_values, final_survives, final_eliminated_by = filter_candidates(
        start,
        end,
        primes,
    )

    final_prime = primes[-1]

    final_remaining = int(np.count_nonzero(final_survives))

    final_removed = int(np.count_nonzero(final_eliminated_by == final_prime))

    figure = build_candidate_figure(
        final_values,
        final_survives,
        final_eliminated_by,
        final_prime,
    )

    figure.update_layout(
        height=720,
        margin={
            "l": 10,
            "r": 10,
            "t": 70,
            "b": 125,
        },
        annotations=_status_annotation(
            f"Filter {final_prime}  |  "
            f"removed {final_removed:,}  |  "
            f"remaining {final_remaining:,}"
        ),
    )

    frames = []
    frame_names = []
    slider_steps = []

    start_values, start_survives, start_eliminated_by = filter_candidates(
        start,
        end,
        (),
    )

    start_candidates = int(np.count_nonzero(start_survives))

    start_figure = build_candidate_figure(
        start_values,
        start_survives,
        start_eliminated_by,
        None,
    )

    frames.append(
        go.Frame(
            name="start",
            data=[
                start_figure.data[0],
            ],
            traces=[0],
            layout=go.Layout(
                annotations=_status_annotation(
                    f"Start  |  " f"{start_candidates:,} candidates"
                )
            ),
        )
    )

    frame_names.append("start")

    slider_steps.append(
        {
            "label": "Start",
            "method": "animate",
            "args": [
                ["start"],
                {
                    "frame": {
                        "duration": 0,
                        "redraw": True,
                    },
                    "transition": {
                        "duration": 0,
                    },
                    "mode": "immediate",
                },
            ],
        }
    )

    for step, prime in enumerate(primes):
        stage_primes = primes[: step + 1]

        (
            stage_values,
            stage_survives,
            stage_eliminated_by,
        ) = filter_candidates(
            start,
            end,
            stage_primes,
        )

        removed_now = int(np.count_nonzero(stage_eliminated_by == prime))

        remaining_now = int(np.count_nonzero(stage_survives))

        stage_figure = build_candidate_figure(
            stage_values,
            stage_survives,
            stage_eliminated_by,
            prime,
        )

        frame_name = f"prime_{prime}"

        frames.append(
            go.Frame(
                name=frame_name,
                data=[
                    stage_figure.data[0],
                ],
                traces=[0],
                layout=go.Layout(
                    annotations=_status_annotation(
                        f"Filter {prime}  |  "
                        f"removed {removed_now:,}  |  "
                        f"remaining {remaining_now:,}"
                    )
                ),
            )
        )

        frame_names.append(frame_name)

        slider_steps.append(
            {
                "label": str(prime),
                "method": "animate",
                "args": [
                    [frame_name],
                    {
                        "frame": {
                            "duration": 0,
                            "redraw": True,
                        },
                        "transition": {
                            "duration": 0,
                        },
                        "mode": "immediate",
                    },
                ],
            }
        )

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
                "pad": {
                    "t": 55,
                    "r": 10,
                },
                "buttons": [
                    {
                        "label": "▶ Replay",
                        "method": "animate",
                        "args": [
                            frame_names,
                            {
                                "frame": {
                                    "duration": 600,
                                    "redraw": True,
                                },
                                "transition": {
                                    "duration": 0,
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
                                "frame": {
                                    "duration": 0,
                                    "redraw": True,
                                },
                                "transition": {
                                    "duration": 0,
                                },
                                "mode": "immediate",
                            },
                        ],
                    },
                ],
            }
        ],
        sliders=[
            {
                "active": len(slider_steps) - 1,
                "x": 0.18,
                "y": 0,
                "len": 0.82,
                "xanchor": "left",
                "yanchor": "top",
                "pad": {
                    "t": 48,
                },
                "currentvalue": {
                    "prefix": "Filter stage: ",
                    "visible": True,
                    "xanchor": "right",
                },
                "steps": slider_steps,
            }
        ],
    )

    return figure
