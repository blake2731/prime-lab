from collections.abc import Sequence

import numpy as np
import plotly.graph_objects as go

from prime_lab.certification import (
    certification_frontier,
    confirmed_prime_mask,
)
from prime_lab.filters import filter_candidates
from ui.residue_structure import (
    MODULUS,
    PRIME_ELIGIBLE_RESIDUES,
    build_residue_figure,
)


def _phase_count(
    event_count: int,
    maximum: int,
) -> int:
    """Choose a bounded number of deterministic reveal phases."""

    if event_count <= 0:
        return 0

    return min(
        maximum,
        max(
            1,
            int(np.ceil(np.sqrt(event_count))),
        ),
    )


def _interleaved_batches(
    indices: np.ndarray,
    phase_count: int,
) -> list[np.ndarray]:
    """Split ordered events into reproducible scattered batches."""

    if phase_count <= 0:
        return []

    return [
        indices[offset::phase_count]
        for offset in range(phase_count)
    ]


def _frame(
    name: str,
    source: go.Figure,
    title: str,
) -> go.Frame:
    """Build one animated residue state."""

    return go.Frame(
        name=name,
        data=[
            source.data[0],
            source.data[1],
            source.data[2],
        ],
        traces=[
            0,
            1,
            2,
        ],
        layout=go.Layout(
            title={
                "text": title,
                "x": 0.99,
                "xanchor": "right",
                "y": 0.99,
                "yanchor": "top",
                "font": {
                    "size": 14,
                    "color": "#566173",
                },
            }
        ),
    )


def _slider_step(
    label: str,
    frame_name: str,
) -> dict:
    """Create one exact prime checkpoint on the animation timeline."""

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


def _settled_title(
    prime: int,
    frontier: int,
    modulus: int,
    remaining: int,
    confirmed: int,
) -> str:
    """Describe the mathematical structure after one filter settles."""

    if (
        modulus == MODULUS
        and prime == 5
    ):
        return (
            "Filter 5 complete  ·  modulo 30 wheel formed  ·  "
            f"{len(PRIME_ELIGIBLE_RESIDUES)} of 30 residue corridors "
            "remain prime eligible above 5"
        )

    if prime > 5:
        return (
            f"Filter {prime} complete  ·  "
            f"{remaining:,} candidates remain  ·  "
            f"{confirmed:,} confirmed  ·  "
            f"proof frontier n < {frontier:,}"
        )

    return (
        f"Filter {prime} complete  ·  "
        f"proof frontier n < {frontier:,}"
    )


def build_residue_animation(
    start: int,
    end: int,
    filter_primes: Sequence[int],
    modulus: int = MODULUS,
) -> go.Figure:
    """Animate residue corridors using deterministic mathematical events."""

    primes = tuple(filter_primes)

    if not primes:
        values, survives, eliminated_by = filter_candidates(
            start,
            end,
            (),
        )

        confirmed = np.zeros(
            values.shape,
            dtype=bool,
        )

        return build_residue_figure(
            values,
            survives,
            eliminated_by,
            confirmed,
            None,
            modulus,
        )

    (
        final_values,
        final_survives,
        final_eliminated_by,
    ) = filter_candidates(
        start,
        end,
        primes,
    )

    final_confirmed = confirmed_prime_mask(
        final_values,
        final_survives,
        primes,
    )

    final_frontier = certification_frontier(
        primes
    )

    figure = build_residue_figure(
        final_values,
        final_survives,
        final_eliminated_by,
        final_confirmed,
        None,
        modulus,
    )

    final_title = _settled_title(
        primes[-1],
        final_frontier,
        modulus,
        int(np.count_nonzero(final_survives)),
        int(np.count_nonzero(final_confirmed)),
    )

    figure.update_layout(
        height=750,
        margin={
            "l": 55,
            "r": 20,
            "t": 125,
            "b": 105,
        },
        title={
            "text": final_title,
            "x": 0.99,
            "xanchor": "right",
            "y": 0.99,
            "yanchor": "top",
            "font": {
                "size": 14,
                "color": "#566173",
            },
        },
    )

    frames: list[go.Frame] = []
    playback_names: list[str] = []
    slider_steps: list[dict] = []

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

    start_figure = build_residue_figure(
        previous_values,
        previous_survives,
        previous_eliminated_by,
        previous_confirmed,
        None,
        modulus,
    )

    frames.append(
        _frame(
            "start",
            start_figure,
            "Start  ·  every integer greater than 1 begins as a candidate",
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

        elimination_phase_count = _phase_count(
            len(new_eliminated),
            maximum=6,
        )

        elimination_batches = _interleaved_batches(
            new_eliminated,
            elimination_phase_count,
        )

        partial_survives = previous_survives.copy()
        partial_eliminated_by = previous_eliminated_by.copy()

        resolved_count = 0

        for phase, batch in enumerate(
            elimination_batches,
            start=1,
        ):
            partial_survives[batch] = False
            partial_eliminated_by[batch] = prime

            resolved_count += len(batch)

            current_mask = np.zeros(
                stage_values.shape,
                dtype=bool,
            )
            current_mask[batch] = True

            drop_figure = build_residue_figure(
                stage_values,
                partial_survives,
                partial_eliminated_by,
                previous_confirmed,
                prime,
                modulus,
                current_elimination=current_mask,
            )

            frame_name = (
                f"prime_{prime}_drop_{phase}"
            )

            frames.append(
                _frame(
                    frame_name,
                    drop_figure,
                    (
                        f"Filter {prime}  ·  composite rainfall "
                        f"{phase}/{elimination_phase_count}  ·  "
                        f"{resolved_count:,} of {len(new_eliminated):,} "
                        "new composites resolved"
                    ),
                )
            )

            playback_names.append(
                frame_name
            )

        certification_phase_count = _phase_count(
            len(new_confirmed),
            maximum=4,
        )

        certification_batches = _interleaved_batches(
            new_confirmed,
            certification_phase_count,
        )

        partial_confirmed = previous_confirmed.copy()
        revealed_count = 0

        for phase, batch in enumerate(
            certification_batches,
            start=1,
        ):
            partial_confirmed[batch] = True
            revealed_count += len(batch)

            certification_figure = build_residue_figure(
                stage_values,
                stage_survives,
                stage_eliminated_by,
                partial_confirmed,
                None,
                modulus,
            )

            frame_name = (
                f"prime_{prime}_confirm_{phase}"
            )

            frames.append(
                _frame(
                    frame_name,
                    certification_figure,
                    (
                        f"Filter {prime} complete  ·  prime certification "
                        f"{phase}/{certification_phase_count}  ·  "
                        f"{revealed_count:,} of {len(new_confirmed):,} "
                        f"new primes revealed  ·  n < {frontier:,}"
                    ),
                )
            )

            playback_names.append(
                frame_name
            )

        settled_figure = build_residue_figure(
            stage_values,
            stage_survives,
            stage_eliminated_by,
            stage_confirmed,
            None,
            modulus,
        )

        settled_name = (
            f"prime_{prime}_settle"
        )

        settled_title = _settled_title(
            prime,
            frontier,
            modulus,
            int(np.count_nonzero(stage_survives)),
            int(np.count_nonzero(stage_confirmed)),
        )

        frames.append(
            _frame(
                settled_name,
                settled_figure,
                settled_title,
            )
        )

        playback_names.append(
            settled_name
        )

        slider_steps.append(
            _slider_step(
                str(prime),
                settled_name,
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
                    "t": 58,
                    "r": 10,
                },
                "buttons": [
                    {
                        "label": "▶ Replay structure",
                        "method": "animate",
                        "args": [
                            playback_names,
                            {
                                "frame": {
                                    "duration": 210,
                                    "redraw": True,
                                },
                                "transition": {
                                    "duration": 70,
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
                "x": 0.2,
                "y": 0,
                "len": 0.8,
                "xanchor": "left",
                "yanchor": "top",
                "pad": {
                    "t": 50,
                },
                "currentvalue": {
                    "prefix": "Resolved through prime: ",
                    "visible": True,
                    "xanchor": "right",
                },
                "steps": slider_steps,
            }
        ],
    )

    return figure
