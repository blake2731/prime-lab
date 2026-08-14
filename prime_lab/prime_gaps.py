from dataclasses import dataclass
from math import log

import numpy as np


@dataclass(frozen=True)
class PrimeGapRecord:
    """One gap between consecutive confirmed primes in the visible range."""

    lower_prime: int
    upper_prime: int
    gap: int
    log_scale: float
    normalized_gap: float
    is_twin_pair: bool
    is_local_record: bool


@dataclass(frozen=True)
class PrimeGapSummary:
    """Descriptive statistics for a sequence of confirmed prime gaps."""

    gap_count: int
    mean_gap: float
    median_gap: float
    largest_gap: int
    largest_gap_lower_prime: int
    largest_gap_upper_prime: int
    twin_pair_count: int
    largest_normalized_gap: float
    largest_normalized_lower_prime: int
    largest_normalized_upper_prime: int


def confirmed_prime_values(
    values: np.ndarray,
    confirmed: np.ndarray,
) -> np.ndarray:
    """Return confirmed prime values in ascending order."""

    values_array = np.asarray(values)
    confirmed_array = np.asarray(
        confirmed,
        dtype=bool,
    )

    if values_array.shape != confirmed_array.shape:
        raise ValueError(
            "values and confirmed must have matching shapes"
        )

    prime_values = values_array[
        confirmed_array
    ].astype(
        np.int64,
        copy=False,
    )

    if len(prime_values) <= 1:
        return prime_values.copy()

    return np.sort(prime_values)


def prime_gap_records(
    values: np.ndarray,
    confirmed: np.ndarray,
) -> tuple[PrimeGapRecord, ...]:
    """Measure gaps between consecutive confirmed primes in the visible range."""

    primes = confirmed_prime_values(
        values,
        confirmed,
    )

    if len(primes) < 2:
        return ()

    records: list[PrimeGapRecord] = []
    local_record_gap = -1

    for lower_value, upper_value in zip(
        primes[:-1],
        primes[1:],
        strict=True,
    ):
        lower_prime = int(lower_value)
        upper_prime = int(upper_value)
        gap = upper_prime - lower_prime

        if gap <= 0:
            raise ValueError(
                "confirmed prime values must be distinct"
            )

        log_scale = log(lower_prime)
        normalized_gap = gap / log_scale
        is_local_record = gap > local_record_gap

        if is_local_record:
            local_record_gap = gap

        records.append(
            PrimeGapRecord(
                lower_prime=lower_prime,
                upper_prime=upper_prime,
                gap=gap,
                log_scale=log_scale,
                normalized_gap=normalized_gap,
                is_twin_pair=(gap == 2),
                is_local_record=is_local_record,
            )
        )

    return tuple(records)


def summarize_prime_gaps(
    records: tuple[PrimeGapRecord, ...],
) -> PrimeGapSummary | None:
    """Summarize a nonempty sequence of prime gap records."""

    if not records:
        return None

    gaps = np.asarray(
        [
            record.gap
            for record in records
        ],
        dtype=np.float64,
    )

    largest_record = max(
        records,
        key=lambda record: (
            record.gap,
            -record.lower_prime,
        ),
    )

    largest_normalized_record = max(
        records,
        key=lambda record: (
            record.normalized_gap,
            -record.lower_prime,
        ),
    )

    return PrimeGapSummary(
        gap_count=len(records),
        mean_gap=float(np.mean(gaps)),
        median_gap=float(np.median(gaps)),
        largest_gap=largest_record.gap,
        largest_gap_lower_prime=largest_record.lower_prime,
        largest_gap_upper_prime=largest_record.upper_prime,
        twin_pair_count=sum(
            record.is_twin_pair
            for record in records
        ),
        largest_normalized_gap=(
            largest_normalized_record.normalized_gap
        ),
        largest_normalized_lower_prime=(
            largest_normalized_record.lower_prime
        ),
        largest_normalized_upper_prime=(
            largest_normalized_record.upper_prime
        ),
    )


def gap_frequency(
    records: tuple[PrimeGapRecord, ...],
) -> tuple[tuple[int, int], ...]:
    """Count how often each observed confirmed prime gap occurs."""

    counts: dict[int, int] = {}

    for record in records:
        counts[record.gap] = (
            counts.get(record.gap, 0)
            + 1
        )

    return tuple(
        sorted(counts.items())
    )
