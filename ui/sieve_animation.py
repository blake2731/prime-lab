from collections.abc import Sequence

import numpy as np
import plotly.graph_objects as go

from prime_lab.certification import (
    certification_frontier,
    confirmed_prime_mask,
)
from prime_lab.filters import filter_candidates
from ui.candidate_grid import build_candidate_figure


WAVE_SLICES = 8


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


def _wave_ranges(
    count: int,
) -> list[tuple[int, int]]:
    """Divide the ordered number field into contiguous wave bands."""

    slice_count = min(
        WAVE_SLICES,
        count,
    )

    edges = np.linspace(
        0,
        count,
        slice_count + 1,
        dtype=int,
    )

    return [
        (int(start), int(end))
        for start, end in zip(
            edges[:-1],
            edges[1:],
        )
        if end > start
    ]


def build_sieve_animation(
    start: int,
    end: int,
    filter_primes: Sequence[int],
) -> go.Figure:
    """Build a wave based browser controlled sieve animation."""

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

    final_remaining = int(
        np.count_nonzero(
            final_survives
        )
    )

    final_removed = int(
        np.count_nonzero(
            final_eliminated_by == final_prime
        )
    )

    final_confirmed = confirmed_prime_mask(
        final_values,
        final_survives,
        primes,
    )

    final_confirmed_count = int(
        np.count_nonzero(
            final_confirmed
        )
    )

    final_frontier = certification_frontier(
        primes
    )

    figure = build_candidate_figure(
        final_values,
        final_survives,
        final_eliminated_by,
        None,
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
            f"Filter {final_prime} complete  |  "
            f"removed {final_removed:,}  |  "
            f"remaining {final_remaining:,}  |  "
            f"confirmed {final_confirmed_count:,}  |  "
            f"proof frontier n < {final_frontier:,}"
        ),
    )

    frames = []
    playback_names = []
    slider_steps = []

    (
        before_values,
        before_survives,
        before_eliminated_by,
    ) = filter_candidates(
        start,
        end,
        (),
    )

    before_confirmed = np.zeros(
        before_values.shape,
        dtype=bool,
    )

    start_candidates = int(
        np.count_nonzero(
            before_survives
        )
    )

    start_figure = build_candidate_figure(
        before_values,
        before_survives,
        before_eliminated_by,
        None,
        before_confirmed,
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

        stage_confirmed = confirmed_prime_mask(
            stage_values,
            stage_survives,
            stage_primes,
        )

        frontier = certification_frontier(
            stage_primes
        )

        newly_eliminated = (
            stage_eliminated_by == prime
        )

        newly_confirmed = (
            stage_confirmed
            & ~before_confirmed
        )

        wave_ranges = _wave_ranges(
            len(stage_values)
        )

        for wave_index, (
            band_start,
            band_end,
        ) in enumerate(
            wave_ranges,
            start=1,
        ):
            scan_survives = before_survives.copy()
            scan_eliminated_by = before_eliminated_by.copy()
            scan_confirmed = before_confirmed.copy()

            scan_survives[:band_start] = stage_survives[:band_start]
            scan_eliminated_by[:band_start] = stage_eliminated_by[:band_start]
            scan_confirmed[:band_start] = stage_confirmed[:band_start]

            scan_mask = np.zeros(
                stage_values.shape,
                dtype=bool,
            )

            scan_mask[
                band_start:band_end
            ] = True

            no_active_eliminations = np.zeros(
                stage_values.shape,
                dtype=bool,
            )

            scan_figure = build_candidate_figure(
                stage_values,
                scan_survives,
                scan_eliminated_by,
                prime,
                scan_confirmed,
                active_elimination_mask=no_active_eliminations,
                scan_mask=scan_mask,
                include_hover=False,
            )

            scan_name = (
                f"prime_{prime}_scan_{wave_index}"
            )

            scan_start_value = int(
                stage_values[band_start]
            )

            scan_end_value = int(
                stage_values[band_end - 1]
            )

            frames.append(
                _animation_frame(
                    scan_name,
                    scan_figure,
                    f"Filter {prime} scanning  |  "
                    f"testing {scan_start_value:,} to {scan_end_value:,}  |  "
                    f"wave {wave_index}/{len(wave_ranges)}",
                )
            )

            playback_names.append(
                scan_name
            )

            resolve_survives = before_survives.copy()
            resolve_eliminated_by = before_eliminated_by.copy()
            resolve_confirmed = before_confirmed.copy()

            resolve_survives[:band_end] = stage_survives[:band_end]
            resolve_eliminated_by[:band_end] = stage_eliminated_by[:band_end]
            resolve_confirmed[:band_end] = stage_confirmed[:band_end]

            active_eliminations = np.zeros(
                stage_values.shape,
                dtype=bool,
            )

            active_eliminations[
                band_start:band_end
            ] = newly_eliminated[
                band_start:band_end
            ]

            resolved_removed = int(
                np.count_nonzero(
                    newly_eliminated[:band_end]
                )
            )

            resolved_confirmed = int(
                np.count_nonzero(
                    newly_confirmed[:band_end]
                )
            )

            resolve_figure = build_candidate_figure(
                stage_values,
                resolve_survives,
                resolve_eliminated_by,
                prime,
                resolve_confirmed,
                active_elimination_mask=active_eliminations,
                include_hover=False,
            )

            resolve_name = (
                f"prime_{prime}_resolve_{wave_index}"
            )

            frames.append(
                _animation_frame(
                    resolve_name,
                    resolve_figure,
                    f"Filter {prime} resolving  |  "
                    f"resolved through {scan_end_value:,}  |  "
                    f"new composites {resolved_removed:,}  |  "
                    f"new primes {resolved_confirmed:,}",
                )
            )

            playback_names.append(
                resolve_name
            )

        stage_remaining = int(
            np.count_nonzero(
                stage_survives
            )
        )

        stage_removed = int(
            np.count_nonzero(
                newly_eliminated
            )
        )

        stage_confirmed_count = int(
            np.count_nonzero(
                stage_confirmed
            )
        )

        complete_figure = build_candidate_figure(
            stage_values,
            stage_survives,
            stage_eliminated_by,
            None,
            stage_confirmed,
        )

        complete_name = (
            f"prime_{prime}_complete"
        )

        frames.append(
            _animation_frame(
                complete_name,
                complete_figure,
                f"Filter {prime} complete  |  "
                f"removed {stage_removed:,}  |  "
                f"remaining {stage_remaining:,}  |  "
                f"confirmed {stage_confirmed_count:,}  |  "
                f"proof frontier n < {frontier:,}",
            )
        )

        playback_names.append(
            complete_name
        )

        slider_steps.append(
            _slider_step(
                str(prime),
                complete_name,
            )
        )

        before_values = stage_values
        before_survives = stage_survives
        before_eliminated_by = stage_eliminated_by
        before_confirmed = stage_confirmed

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
                                    "duration": 90,
                                    "redraw": True,
                                },
                                "transition": {
                                    "duration": 45,
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
                    "prefix": "Completed filter: ",
                    "visible": True,
                    "xanchor": "right",
                },
                "steps": slider_steps,
            }
        ],
    )

    return figure
