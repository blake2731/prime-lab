from io import BytesIO
import wave

import numpy as np
import pytest

from prime_lab.certification import confirmed_prime_mask
from prime_lab.filters import filter_candidates
from prime_lab.sonification import (
    PENTATONIC_NOTE_NAMES,
    PRIME_ELIGIBLE_RESIDUES,
    midi_frequency,
    prime_gap_events,
    prime_note,
    render_prime_gap_wav,
)


def _confirmed_through_five():
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

    return values, confirmed


def test_midi_frequency_places_a4_at_440_hz():
    assert midi_frequency(69) == pytest.approx(
        440.0
    )


def test_modulo_30_prime_lanes_map_to_ordered_pentatonic_notes():
    mapped_notes = []

    for residue in PRIME_ELIGIBLE_RESIDUES:
        _, note_name, _, _ = prime_note(
            residue
        )

        mapped_notes.append(
            note_name
        )

    assert tuple(mapped_notes) == PENTATONIC_NOTE_NAMES


def test_prime_gap_events_preserve_exact_confirmed_values_and_gaps():
    values, confirmed = _confirmed_through_five()

    events = prime_gap_events(
        values,
        confirmed,
    )

    sounding_values = [
        event.value
        for event in events
    ]

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

    assert [
        event.gap
        for event in events
    ] == [
        None,
        1,
        2,
        2,
        4,
        2,
        4,
        2,
        4,
        6,
        2,
        6,
        4,
        2,
        4,
    ]


def test_prime_gap_wav_is_deterministic_valid_stereo_audio():
    values, confirmed = _confirmed_through_five()

    first = render_prime_gap_wav(
        values,
        confirmed,
        bpm=360,
    )

    second = render_prime_gap_wav(
        values,
        confirmed,
        bpm=360,
    )

    assert first == second
    assert first[:4] == b"RIFF"
    assert first[8:12] == b"WAVE"

    with wave.open(
        BytesIO(first),
        "rb",
    ) as wav_file:
        assert wav_file.getnchannels() == 2
        assert wav_file.getsampwidth() == 2
        assert wav_file.getframerate() == 22050
        assert wav_file.getnframes() > 0


def test_prime_gap_wav_returns_empty_when_nothing_is_confirmed():
    values = np.arange(
        1,
        31,
        dtype=np.int64,
    )

    confirmed = np.zeros(
        values.shape,
        dtype=bool,
    )

    assert render_prime_gap_wav(
        values,
        confirmed,
    ) == b""
