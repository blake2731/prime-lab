import numpy as np
import pytest

from prime_lab.certification import confirmed_prime_mask
from prime_lab.filters import filter_candidates
from prime_lab.prime_gaps import (
    confirmed_prime_values,
    gap_frequency,
    prime_gap_records,
    summarize_prime_gaps,
)


def _confirmed_through_30():
    primes = (
        2,
        3,
        5,
    )

    values, survives, _ = filter_candidates(
        1,
        30,
        primes,
    )

    confirmed = confirmed_prime_mask(
        values,
        survives,
        primes,
    )

    return values, confirmed


def test_confirmed_prime_values_are_exact_through_30():
    values, confirmed = _confirmed_through_30()

    assert confirmed_prime_values(
        values,
        confirmed,
    ).tolist() == [
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
    ]


def test_prime_gap_records_are_exact_through_30():
    values, confirmed = _confirmed_through_30()

    records = prime_gap_records(
        values,
        confirmed,
    )

    assert [
        record.gap
        for record in records
    ] == [
        1,
        2,
        2,
        4,
        2,
        4,
        2,
        4,
        6,
    ]

    assert [
        record.gap
        for record in records
        if record.is_local_record
    ] == [
        1,
        2,
        4,
        6,
    ]

    assert all(
        record.normalized_gap > 0
        for record in records
    )


def test_gap_summary_counts_twin_pairs_and_largest_gap():
    values, confirmed = _confirmed_through_30()

    records = prime_gap_records(
        values,
        confirmed,
    )

    summary = summarize_prime_gaps(
        records
    )

    assert summary is not None
    assert summary.gap_count == 9
    assert summary.twin_pair_count == 4
    assert summary.most_common_gap == 2
    assert summary.most_common_gap_count == 4
    assert summary.largest_gap == 6
    assert summary.largest_gap_lower_prime == 23
    assert summary.largest_gap_upper_prime == 29
    assert summary.mean_gap == pytest.approx(3.0)
    assert summary.median_gap == pytest.approx(2.0)


def test_gap_frequency_counts_each_observed_size():
    values, confirmed = _confirmed_through_30()

    records = prime_gap_records(
        values,
        confirmed,
    )

    assert gap_frequency(records) == (
        (1, 1),
        (2, 4),
        (4, 3),
        (6, 1),
    )


def test_gap_analysis_ignores_unresolved_survivors():
    values, survives, _ = filter_candidates(
        1,
        100,
        (
            2,
            3,
        ),
    )

    confirmed = confirmed_prime_mask(
        values,
        survives,
        (
            2,
            3,
        ),
    )

    confirmed_values = confirmed_prime_values(
        values,
        confirmed,
    )

    assert confirmed_values.tolist() == [
        2,
        3,
        5,
        7,
        11,
        13,
        17,
        19,
        23,
    ]

    assert 29 not in confirmed_values


def test_gap_analysis_rejects_shape_mismatch():
    values = np.arange(
        1,
        11,
        dtype=np.int64,
    )

    confirmed = np.zeros(
        9,
        dtype=bool,
    )

    with pytest.raises(
        ValueError,
        match="matching shapes",
    ):
        prime_gap_records(
            values,
            confirmed,
        )
