from dataclasses import dataclass
from io import BytesIO
from math import cos, pi, sin
import wave

import numpy as np


DEFAULT_MODULUS = 30
DEFAULT_SAMPLE_RATE = 22050
DEFAULT_BPM = 360
MAX_AUDIO_SECONDS = 45.0

PRIME_ELIGIBLE_RESIDUES = (
    1,
    7,
    11,
    13,
    17,
    19,
    23,
    29,
)

PENTATONIC_NOTE_NAMES = (
    "C4",
    "D4",
    "E4",
    "G4",
    "A4",
    "C5",
    "D5",
    "E5",
)

PENTATONIC_MIDI = (
    60,
    62,
    64,
    67,
    69,
    72,
    74,
    76,
)

SPECIAL_PRIME_NOTES = {
    2: (48, "C3"),
    3: (55, "G3"),
    5: (60, "C4"),
}


@dataclass(frozen=True)
class PrimeSoundEvent:
    """One mathematically defined prime event in the audio sequence."""

    value: int
    gap: int | None
    residue: int
    note_name: str
    frequency: float
    pan: float


def midi_frequency(midi_note: int) -> float:
    """Convert a MIDI note number to equal tempered frequency."""

    return 440.0 * (
        2.0 ** ((midi_note - 69) / 12.0)
    )


def prime_note(
    value: int,
    modulus: int = DEFAULT_MODULUS,
) -> tuple[int, str, float, float]:
    """Map prime identity to a stable musical pitch and stereo position."""

    if modulus != DEFAULT_MODULUS:
        raise ValueError(
            "musical prime mapping currently supports modulus 30"
        )

    if value in SPECIAL_PRIME_NOTES:
        midi_note, note_name = SPECIAL_PRIME_NOTES[value]

        return (
            value % modulus,
            note_name,
            midi_frequency(midi_note),
            0.0,
        )

    residue = value % modulus

    if residue not in PRIME_ELIGIBLE_RESIDUES:
        raise ValueError(
            "value is not in a prime eligible residue class modulo 30"
        )

    lane_index = PRIME_ELIGIBLE_RESIDUES.index(
        residue
    )

    midi_note = PENTATONIC_MIDI[
        lane_index
    ]

    note_name = PENTATONIC_NOTE_NAMES[
        lane_index
    ]

    if len(PRIME_ELIGIBLE_RESIDUES) == 1:
        pan = 0.0

    else:
        pan = -0.72 + (
            1.44
            * lane_index
            / (len(PRIME_ELIGIBLE_RESIDUES) - 1)
        )

    return (
        residue,
        note_name,
        midi_frequency(midi_note),
        pan,
    )


def prime_gap_events(
    values: np.ndarray,
    confirmed: np.ndarray,
    modulus: int = DEFAULT_MODULUS,
) -> list[PrimeSoundEvent]:
    """Return confirmed primes with exact consecutive prime gaps."""

    if values.shape != confirmed.shape:
        raise ValueError(
            "values and confirmed must have the same shape"
        )

    confirmed_values = [
        int(value)
        for value in values[
            np.asarray(
                confirmed,
                dtype=bool,
            )
        ]
    ]

    events: list[PrimeSoundEvent] = []
    previous_value: int | None = None

    for value in confirmed_values:
        residue, note_name, frequency, pan = prime_note(
            value,
            modulus,
        )

        gap = (
            None
            if previous_value is None
            else value - previous_value
        )

        events.append(
            PrimeSoundEvent(
                value=value,
                gap=gap,
                residue=residue,
                note_name=note_name,
                frequency=frequency,
                pan=pan,
            )
        )

        previous_value = value

    return events


def _note_envelope(
    sample_count: int,
    sample_rate: int,
) -> np.ndarray:
    """Create a gentle mallet style attack and decay envelope."""

    time = np.arange(
        sample_count,
        dtype=np.float64,
    ) / sample_rate

    attack_seconds = 0.008

    attack = np.minimum(
        time / attack_seconds,
        1.0,
    )

    decay = np.exp(
        -4.6
        * time
        / max(
            time[-1]
            if sample_count > 1
            else attack_seconds,
            attack_seconds,
        )
    )

    return attack * decay


def _synthesize_note(
    frequency: float,
    duration_seconds: float,
    sample_rate: int,
) -> np.ndarray:
    """Synthesize a soft harmonic tone suitable for overlapping melodies."""

    sample_count = max(
        1,
        int(
            round(
                duration_seconds
                * sample_rate
            )
        ),
    )

    time = np.arange(
        sample_count,
        dtype=np.float64,
    ) / sample_rate

    tone = (
        np.sin(
            2.0 * pi * frequency * time
        )
        + 0.24
        * np.sin(
            2.0
            * pi
            * frequency
            * 2.0
            * time
        )
        + 0.08
        * np.sin(
            2.0
            * pi
            * frequency
            * 3.0
            * time
        )
    )

    tone *= _note_envelope(
        sample_count,
        sample_rate,
    )

    return tone


def _equal_power_pan(
    pan: float,
) -> tuple[float, float]:
    """Convert a minus one to one pan position into stereo gains."""

    bounded_pan = min(
        1.0,
        max(
            -1.0,
            pan,
        ),
    )

    angle = (
        bounded_pan + 1.0
    ) * pi / 4.0

    return (
        cos(angle),
        sin(angle),
    )


def _apply_echo(
    audio: np.ndarray,
    sample_rate: int,
) -> np.ndarray:
    """Add a small deterministic room effect without changing event timing."""

    result = audio.copy()

    for delay_seconds, gain in (
        (0.055, 0.12),
        (0.110, 0.055),
    ):
        delay_samples = int(
            round(
                delay_seconds
                * sample_rate
            )
        )

        if delay_samples <= 0:
            continue

        result[
            delay_samples:,
            :
        ] += (
            audio[
                :-delay_samples,
                :
            ]
            * gain
        )

    return result


def render_prime_gap_wav(
    values: np.ndarray,
    confirmed: np.ndarray,
    modulus: int = DEFAULT_MODULUS,
    bpm: int = DEFAULT_BPM,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    max_audio_seconds: float = MAX_AUDIO_SECONDS,
) -> bytes:
    """Render pentatonic residue pitch with exact prime gaps as rhythm."""

    if bpm <= 0:
        raise ValueError("bpm must be positive")

    if sample_rate < 8000:
        raise ValueError(
            "sample_rate must be at least 8000"
        )

    if max_audio_seconds <= 1.0:
        raise ValueError(
            "max_audio_seconds must be greater than 1"
        )

    events = prime_gap_events(
        values,
        confirmed,
        modulus,
    )

    if not events:
        return b""

    first_value = events[0].value
    last_value = events[-1].value

    nominal_seconds_per_integer = (
        60.0 / bpm / 4.0
    )

    integer_span = max(
        1,
        last_value - first_value,
    )

    note_duration = min(
        0.34,
        max(
            0.11,
            nominal_seconds_per_integer * 3.0,
        ),
    )

    maximum_timeline = max(
        0.25,
        max_audio_seconds
        - note_duration
        - 0.15,
    )

    seconds_per_integer = min(
        nominal_seconds_per_integer,
        maximum_timeline / integer_span,
    )

    total_seconds = (
        integer_span
        * seconds_per_integer
        + note_duration
        + 0.15
    )

    total_samples = max(
        1,
        int(
            np.ceil(
                total_seconds
                * sample_rate
            )
        ),
    )

    audio = np.zeros(
        (
            total_samples,
            2,
        ),
        dtype=np.float64,
    )

    for event in events:
        onset_seconds = (
            event.value - first_value
        ) * seconds_per_integer

        start_sample = int(
            round(
                onset_seconds
                * sample_rate
            )
        )

        note = _synthesize_note(
            event.frequency,
            note_duration,
            sample_rate,
        )

        end_sample = min(
            total_samples,
            start_sample + len(note),
        )

        note = note[
            : end_sample - start_sample
        ]

        left_gain, right_gain = _equal_power_pan(
            event.pan
        )

        audio[
            start_sample:end_sample,
            0,
        ] += note * left_gain

        audio[
            start_sample:end_sample,
            1,
        ] += note * right_gain

    audio = _apply_echo(
        audio,
        sample_rate,
    )

    peak = float(
        np.max(
            np.abs(audio)
        )
    )

    if peak > 0:
        audio *= 0.9 / peak

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
        wav_file.setnchannels(2)
        wav_file.setsampwidth(2)
        wav_file.setframerate(
            sample_rate
        )
        wav_file.writeframes(
            pcm.tobytes()
        )

    return buffer.getvalue()
