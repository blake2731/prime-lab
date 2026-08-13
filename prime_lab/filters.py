from collections.abc import Iterable

import numpy as np


def filter_candidates(
    start: int,
    end: int,
    filter_primes: Iterable[int],
):
    """Filter integers using known small prime divisors."""

    if start > end:
        raise ValueError("start must not be greater than end")

    values = np.arange(
        start,
        end + 1,
        dtype=np.int64,
    )

    survives = values >= 2

    eliminated_by = np.zeros(
        values.shape,
        dtype=np.int64,
    )

    for prime in filter_primes:
        newly_eliminated = survives & (values != prime) & (values % prime == 0)

        eliminated_by[newly_eliminated] = prime
        survives[newly_eliminated] = False

    return values, survives, eliminated_by
