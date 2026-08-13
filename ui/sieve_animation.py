from collections.abc import Sequence

import numpy as np
import plotly.graph_objects as go

from prime_lab.certification import (
    certification_frontier,
    confirmed_prime_mask,
)
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


def _animation_frame(
    name: str,
    figure: go.Figure,
    status: str,
) -> go.Frame:
    """Create one visual phase of the sieve playback."""

    return go.Frame(
        name=name,
        data=[
            figure.data[0],
        ],
        traces=[0],
        layout=go.Layout(
            annotations=_status_annotation(status)
        ),
    )


def _slider_step(
    label: str,
    frame_name: str,
) -> dict:
    """Create one direct inspection step on the filter timeline."""

    return {
        "label": label,
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


def build_sieve_animation(
    start: int,
    end: int,
    filter_primes: Sequence[int],
) -> go.Figure:
    """Build a two phase browser controlled sieve animation."""

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

    final_confirmed = confirmed_prime_mask(
        final_values,
        final_survives,
        primes,
    )

    final_confirmed_count = int(np.count_nonzero(final_confirmed))

    final_frontier = certification_frontier(primes)

    figure = build_candidate_figure(
        final_values,
        final_survives,
        final_eliminated_by,
        final_prime,
        final_confirmed,
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
            f"remaining {final_remaining:,}  |  "
            f"confirmed {final_confirmed_count:,}  |  "
            f"proof frontier n < {final_frontier:,}"
        ),
    )

    frames = []
    playback_names = []
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
        _animation_frame(
            "start",
            start_figure,
            f"Start  |  {start_candidates:,} candidates  |  no filters applied",
        )
    )

    playback_names.append("start")

    slider_steps.append(
        _slider_step(
            "Start",
            "start",
        )
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

        removed_now = int(
            np.count_nonzero(
                stage_eliminated_by == prime
            )
        )

        remaining_now = int(
            np.count_nonzero(
                stage_survives
            )
        )

        confirmed_now = confirmed_prime_mask(
            stage_values,
            stage_survives,
            stage_primes,
        )

        confirmed_count = int(
            np.count_nonzero(
                confirmed_now
            )
        )

        frontier = certification_frontier(
            stage_primes
        )

        hit_figure = build_candidate_figure(
            stage_values,
            stage_survives,
            stage_eliminated_by,
            prime,
            confirmed_now,
        )

        hit_name = f"prime_{prime}_hit"

        frames.append(
            _animation_frame(
                hit_name,
                hit_figure,
                f"Filter {prime} strikes  |  "
                f"{removed_now:,} newly eliminated  |  "
                f"{confirmed_count:,} primes confirmed  |  "
                f"proof frontier n < {frontier:,}",
            )
        )

        playback_names.append(hit_name)

        slider_steps.append(
            _slider_step(
                str(prime),
                hit_name,
            )
        )

        if prime != primes[-1]:
            settle_figure = build_candidate_figure(
                stage_values,
                stage_survives,
                stage_eliminated_by,
                None,
                confirmed_now,
            )

            settle_name = f"prime_{prime}_settle"

            frames.append(
                _animation_frame(
                    settle_name,
                    settle_figure,
                    f"Resolved through {prime}  |  "
                    f"{remaining_now:,} candidates remain  |  "
                    f"{confirmed_count:,} confirmed primes",
                )
            )

            playback_names.append(settle_name)

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
                            playback_names,
                            {
                                "frame": {
                                    "duration": 420,
                                    "redraw": True,
                                },
                                "transition": {
                                    "duration": 140,
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
                    "prefix": "Inspect filter: ",
                    "visible": True,
                    "xanchor": "right",
                },
                "steps": slider_steps,
            }
        ],
    )

    return figure
