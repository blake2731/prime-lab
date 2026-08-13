from collections.abc import Sequence
from math import isqrt

import numpy as np


def _is_prime(value: int) -> bool:
    """Return whether an integer is prime."""

    if value < 2:
        return False

    if value == 2:
        return True

    if value % 2 == 0:
        return False

    limit = isqrt(value)

    for divisor in range(3, limit + 1, 2):
        if value % divisor == 0:
            return False

    return True


def next_prime_after(value: int) -> int:
    """Return the smallest prime greater than value."""

    candidate = value + 1

    while not _is_prime(candidate):
        candidate += 1

    return candidate


def _expected_prime_prefix(
    last_prime: int,
) -> tuple[int, ...]:
    """Return every prime from 2 through last_prime."""

    return tuple(
        value
        for value in range(2, last_prime + 1)
        if _is_prime(value)
    )


def certification_frontier(
    tested_primes: Sequence[int],
) -> int | None:
    """
    Return the exclusive upper bound below which
    every surviving candidate is proven prime.
    """

    primes = tuple(tested_primes)

    if not primes:
        return None

    expected = _expected_prime_prefix(primes[-1])

    if primes != expected:
        raise ValueError(
            "tested_primes must be a complete ascending "
            "prime sequence beginning with 2"
        )

    next_prime = next_prime_after(primes[-1])

    return next_prime ** 2


def confirmed_prime_mask(
    values: np.ndarray,
    survives: np.ndarray,
    tested_primes: Sequence[int],
) -> np.ndarray:
    """
    Mark survivors whose primality is proven
    by the complete filter sequence so far.
    """

    frontier = certification_frontier(tested_primes)

    if frontier is None:
        return np.zeros(
            values.shape,
            dtype=bool,
        )

    return (
        survives
        & (values >= 2)
        & (values < frontier)
    )
