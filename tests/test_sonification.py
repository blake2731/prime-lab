from math import sqrt

import numpy as np
import pytest

from prime_lab.certification import confirmed_prime_mask
from prime_lab.filters import filter_candidates
from prime_lab.sonification import (
    render_residue_wav,
    residue_events,
    residue_frequency,
)


def test_residue_frequency_maps_half_cycle_to_half_octave():
    base = 220.0

    assert residue_frequency(
        0,
        30,
        base,
    ) == pytest.approx(base)

    assert residue_frequency(
        15,
        30,
        base,
    ) == pytest.approx(
        base * sqrt(2.0)
    )


def test_residue_events_include_exact_confirmed_prime_count():
    values, survives, _ = filter_candidates(
        1,
        60,
        (
            2,
            3,
            5,
        ),
    )

    confirmed = confirmed_prime_mask(
        values,
        survives,
        (
            2,
            3,
            5,
        ),
    )

    events = residue_events(
        values,
        confirmed,
    )

    sounding_values = [
        value
        for step_events in events
        for value, _, _ in step_events
    ]

    assert len(sounding_values) == 15

    assert sounding_values == [
        2,
        3,
        5,
        7,
        11,
        13,
        17,
        19,
        23,
        29,
        31,
        37,
        41,
        43,
        47,
    ]


def test_residue_wav_is_deterministic_and_valid():
    values, survives, _ = filter_candidates(
        1,
        60,
        (
            2,
            3,
            5,
        ),
    )

    confirmed = confirmed_prime_mask(
        values,
        survives,
        (
            2,
            3,
            5,
        ),
    )

    first = render_residue_wav(
        values,
        confirmed,
        bpm=240,
    )

    second = render_residue_wav(
        values,
        confirmed,
        bpm=240,
    )

    assert first == second
    assert first[:4] == b"RIFF"
    assert first[8:12] == b"WAVE"
    assert len(first) > 44


def test_residue_wav_returns_empty_when_nothing_is_confirmed():
    values = np.arange(
        1,
        31,
        dtype=np.int64,
    )

    confirmed = np.zeros(
        values.shape,
        dtype=bool,
    )

    assert render_residue_wav(
        values,
        confirmed,
    ) == b""
