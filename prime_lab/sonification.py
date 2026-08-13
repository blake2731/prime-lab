from io import BytesIO
from math import pi
import wave

import numpy as np


DEFAULT_MODULUS = 30
DEFAULT_BASE_FREQUENCY = 220.0
DEFAULT_SAMPLE_RATE = 22050


def residue_frequency(
    residue: int,
    modulus: int = DEFAULT_MODULUS,
    base_frequency: float = DEFAULT_BASE_FREQUENCY,
) -> float:
    """Map one residue position continuously across a single octave."""

    if modulus < 2:
        raise ValueError("modulus must be at least 2")

    if residue < 0 or residue >= modulus:
        raise ValueError(
            "residue must satisfy 0 <= residue < modulus"
        )

    if base_frequency <= 0:
        raise ValueError(
            "base_frequency must be positive"
        )

    return base_frequency * (
        2.0 ** (residue / modulus)
    )


def residue_events(
    values: np.ndarray,
    confirmed: np.ndarray,
    modulus: int = DEFAULT_MODULUS,
    base_frequency: float = DEFAULT_BASE_FREQUENCY,
) -> list[list[tuple[int, int, float]]]:
    """Group confirmed primes by quotient so quotient becomes musical time."""

    if modulus < 2:
        raise ValueError("modulus must be at least 2")

    if values.shape != confirmed.shape:
        raise ValueError(
            "values and confirmed must have the same shape"
        )

    if len(values) == 0:
        return []

    confirmed_indices = np.flatnonzero(
        confirmed
    )

    if len(confirmed_indices) == 0:
        return []

    quotients = values // modulus

    start_quotient = int(
        np.min(quotients)
    )

    last_confirmed_quotient = int(
        np.max(
            quotients[confirmed_indices]
        )
    )

    events: list[
        list[tuple[int, int, float]]
    ] = [
        []
        for _ in range(
            last_confirmed_quotient
            - start_quotient
            + 1
        )
    ]

    for index in confirmed_indices:
        value = int(values[index])
        quotient = int(quotients[index])
        residue = value % modulus

        events[
            quotient - start_quotient
        ].append(
            (
                value,
                residue,
                residue_frequency(
                    residue,
                    modulus,
                    base_frequency,
                ),
            )
        )

    return events


def _note_envelope(
    sample_count: int,
) -> np.ndarray:
    """Create a short attack and release so notes enter and leave softly."""

    envelope = np.ones(
        sample_count,
        dtype=np.float64,
    )

    fade_count = min(
        max(
            int(sample_count * 0.12),
            1,
        ),
        sample_count // 2,
    )

    if fade_count > 0:
        fade = np.linspace(
            0.0,
            1.0,
            fade_count,
            endpoint=False,
        )

        envelope[:fade_count] = fade
        envelope[-fade_count:] = fade[::-1]

    return envelope


def render_residue_wav(
    values: np.ndarray,
    confirmed: np.ndarray,
    modulus: int = DEFAULT_MODULUS,
    bpm: int = 240,
    base_frequency: float = DEFAULT_BASE_FREQUENCY,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
) -> bytes:
    """Render confirmed primes as a deterministic modulo residue sequencer."""

    if bpm <= 0:
        raise ValueError("bpm must be positive")

    if sample_rate < 8000:
        raise ValueError(
            "sample_rate must be at least 8000"
        )

    events = residue_events(
        values,
        confirmed,
        modulus,
        base_frequency,
    )

    if not events:
        return b""

    seconds_per_step = 60.0 / bpm

    samples_per_step = max(
        1,
        int(
            round(
                seconds_per_step
                * sample_rate
            )
        ),
    )

    note_sample_count = max(
        1,
        int(
            samples_per_step * 0.82
        ),
    )

    audio = np.zeros(
        len(events) * samples_per_step,
        dtype=np.float64,
    )

    time = np.arange(
        note_sample_count,
        dtype=np.float64,
    ) / sample_rate

    envelope = _note_envelope(
        note_sample_count
    )

    for step, step_events in enumerate(events):
        if not step_events:
            continue

        chord = np.zeros(
            note_sample_count,
            dtype=np.float64,
        )

        amplitude = 0.62 / np.sqrt(
            len(step_events)
        )

        for _, _, frequency in step_events:
            fundamental = np.sin(
                2.0
                * pi
                * frequency
                * time
            )

            second_harmonic = 0.16 * np.sin(
                2.0
                * pi
                * frequency
                * 2.0
                * time
            )

            chord += amplitude * (
                fundamental
                + second_harmonic
            )

        chord *= envelope

        start_sample = (
            step * samples_per_step
        )

        end_sample = (
            start_sample
            + note_sample_count
        )

        audio[
            start_sample:end_sample
        ] += chord

    peak = float(
        np.max(
            np.abs(audio)
        )
    )

    if peak > 0:
        audio *= 0.92 / peak

    pcm = np.asarray(
        np.round(
            audio * 32767.0
        ),
        dtype=np.int16,
    )

    buffer = BytesIO()

    with wave.open(
        buffer,
        "wb",
    ) as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(
            sample_rate
        )
        wav_file.writeframes(
            pcm.tobytes()
        )

    return buffer.getvalue()
