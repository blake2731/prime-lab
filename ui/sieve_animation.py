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
    """Create one visual state for browser playback."""

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
    """Create one direct inspection step on the prime timeline."""

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


def _phase_count(event_count: int) -> int:
    """Choose a bounded number of visual drops for one filter."""

    if event_count <= 1:
        return 1

    if event_count <= 12:
        return min(4, event_count)

    if event_count <= 60:
        return 5

    if event_count <= 250:
        return 6

    return 7


def _interleaved_batches(
    indices: np.ndarray,
    phase_count: int,
) -> list[np.ndarray]:
    """Distribute ordered events across deterministic scattered batches."""

    return [
        indices[offset::phase_count]
        for offset in range(phase_count)
    ]


def build_sieve_animation(
    start: int,
    end: int,
    filter_primes: Sequence[int],
    grid_width: int | None = None,
) -> go.Figure:
    """Build deterministic rainfall playback for the sieve sequence."""

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
            grid_width=grid_width,
        )

    final_values, final_survives, final_eliminated_by = filter_candidates(
        start,
        end,
        primes,
    )

    final_confirmed = confirmed_prime_mask(
        final_values,
        final_survives,
        primes,
    )

    final_prime = primes[-1]
    final_remaining = int(np.count_nonzero(final_survives))
    final_confirmed_count = int(np.count_nonzero(final_confirmed))
    final_frontier = certification_frontier(primes)

    figure = build_candidate_figure(
        final_values,
        final_survives,
        final_eliminated_by,
        None,
        final_confirmed,
        grid_width=grid_width,
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
            f"Filter {final_prime} complete  |  "
            f"remaining {final_remaining:,}  |  "
            f"confirmed {final_confirmed_count:,}  |  "
            f"proof frontier n < {final_frontier:,}"
        ),
    )

    frames = []
    playback_names = []
    slider_steps = []

    (
        previous_values,
        previous_survives,
        previous_eliminated_by,
    ) = filter_candidates(
        start,
        end,
        (),
    )

    previous_confirmed = np.zeros(
        previous_values.shape,
        dtype=bool,
    )

    start_candidates = int(
        np.count_nonzero(
            previous_survives
        )
    )

    start_figure = build_candidate_figure(
        previous_values,
        previous_survives,
        previous_eliminated_by,
        None,
        previous_confirmed,
        grid_width=grid_width,
    )

    frames.append(
        _animation_frame(
            "start",
            start_figure,
            f"Start  |  {start_candidates:,} candidates",
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

        stage_confirmed = confirmed_prime_mask(
            stage_values,
            stage_survives,
            stage_primes,
        )

        frontier = certification_frontier(
            stage_primes
        )

        new_eliminated = np.flatnonzero(
            previous_survives
            & ~stage_survives
        )

        new_confirmed = np.flatnonzero(
            stage_confirmed
            & ~previous_confirmed
        )

        total_events = max(
            len(new_eliminated),
            len(new_confirmed),
        )

        phase_count = _phase_count(
            total_events
        )

        elimination_batches = _interleaved_batches(
            new_eliminated,
            phase_count,
        )

        confirmation_batches = _interleaved_batches(
            new_confirmed,
            phase_count,
        )

        resolved_eliminated = np.zeros(
            stage_values.shape,
            dtype=bool,
        )

        resolved_confirmed = previous_confirmed.copy()

        for phase_index in range(phase_count):
            current_elimination = np.zeros(
                stage_values.shape,
                dtype=bool,
            )

            elimination_batch = elimination_batches[
                phase_index
            ]

            confirmation_batch = confirmation_batches[
                phase_index
            ]

            current_elimination[
                elimination_batch
            ] = True

            resolved_eliminated[
                elimination_batch
            ] = True

            resolved_confirmed[
                confirmation_batch
            ] = True

            phase_survives = previous_survives.copy()
            phase_survives[
                resolved_eliminated
            ] = False

            phase_eliminated_by = previous_eliminated_by.copy()
            phase_eliminated_by[
                resolved_eliminated
            ] = prime

            phase_figure = build_candidate_figure(
                stage_values,
                phase_survives,
                phase_eliminated_by,
                prime,
                resolved_confirmed,
                current_elimination,
                grid_width=grid_width,
            )

            resolved_composite_count = int(
                np.count_nonzero(
                    resolved_eliminated
                )
            )

            new_prime_count = int(
                np.count_nonzero(
                    resolved_confirmed
                    & ~previous_confirmed
                )
            )

            frame_name = (
                f"prime_{prime}_drop_"
                f"{phase_index + 1}"
            )

            frames.append(
                _animation_frame(
                    frame_name,
                    phase_figure,
                    f"Filter {prime} resolving  |  "
                    f"{resolved_composite_count:,}/{len(new_eliminated):,} composites  |  "
                    f"{new_prime_count:,}/{len(new_confirmed):,} new primes  |  "
                    f"frontier n < {frontier:,}",
                )
            )

            playback_names.append(
                frame_name
            )

        settled_figure = build_candidate_figure(
            stage_values,
            stage_survives,
            stage_eliminated_by,
            None,
            stage_confirmed,
            grid_width=grid_width,
        )

        remaining_now = int(
            np.count_nonzero(
                stage_survives
            )
        )

        confirmed_now = int(
            np.count_nonzero(
                stage_confirmed
            )
        )

        settle_name = f"prime_{prime}_settle"

        frames.append(
            _animation_frame(
                settle_name,
                settled_figure,
                f"Filter {prime} complete  |  "
                f"removed {len(new_eliminated):,}  |  "
                f"remaining {remaining_now:,}  |  "
                f"confirmed {confirmed_now:,}  |  "
                f"frontier n < {frontier:,}",
            )
        )

        playback_names.append(
            settle_name
        )

        slider_steps.append(
            _slider_step(
                str(prime),
                settle_name,
            )
        )

        previous_values = stage_values
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
                                    "duration": 130,
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
