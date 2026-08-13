import numpy as np
import pytest

from prime_lab.certification import (
    certification_frontier,
    confirmed_prime_mask,
    next_prime_after,
)
from prime_lab.filters import filter_candidates


def test_next_prime_after():
    assert next_prime_after(2) == 3
    assert next_prime_after(5) == 7
    assert next_prime_after(31) == 37
    assert next_prime_after(67) == 71


def test_certification_frontier():
    assert certification_frontier(()) is None
    assert certification_frontier((2,)) == 9
    assert certification_frontier((2, 3)) == 25
    assert certification_frontier((2, 3, 5)) == 49


def test_incomplete_filter_sequence_is_rejected():
    with pytest.raises(ValueError):
        certification_frontier((2, 5))


def test_filters_through_five_confirm_expected_primes():
    values, survives, _ = filter_candidates(
        1,
        60,
        (2, 3, 5),
    )

    confirmed = confirmed_prime_mask(
        values,
        survives,
        (2, 3, 5),
    )

    assert values[confirmed].tolist() == [
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


def test_53_survives_but_is_not_confirmed_after_five():
    values, survives, _ = filter_candidates(
        1,
        60,
        (2, 3, 5),
    )

    confirmed = confirmed_prime_mask(
        values,
        survives,
        (2, 3, 5),
    )

    index = np.where(values == 53)[0][0]

    assert survives[index]
    assert not confirmed[index]


def test_49_is_eliminated_not_confirmed():
    values, survives, _ = filter_candidates(
        1,
        60,
        (2, 3, 5, 7),
    )

    confirmed = confirmed_prime_mask(
        values,
        survives,
        (2, 3, 5, 7),
    )

    index = np.where(values == 49)[0][0]

    assert not survives[index]
    assert not confirmed[index]


def test_filter_through_67_certifies_entire_5000_range():
    primes = (
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
        53,
        59,
        61,
        67,
    )

    values, survives, _ = filter_candidates(
        1,
        5000,
        primes,
    )

    confirmed = confirmed_prime_mask(
        values,
        survives,
        primes,
    )

    assert np.array_equal(
        confirmed,
        survives,
    )
