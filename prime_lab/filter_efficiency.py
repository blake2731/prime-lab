from dataclasses import dataclass
from collections.abc import Sequence

import numpy as np

from prime_lab.filters import filter_candidates


@dataclass(frozen=True)
class FilterEfficiencyStep:
    """One prime filter's unique contribution to the sieve."""

    prime: int
    candidates_before: int
    removed: int
    candidates_after: int
    marginal_removal_rate: float
    cumulative_survival_rate: float


def filter_efficiency_steps(
    start: int,
    end: int,
    filter_primes: Sequence[int],
) -> tuple[FilterEfficiencyStep, ...]:
    """Measure the unique work performed by each prime filter in order."""

    primes = tuple(filter_primes)

    values, survives, eliminated_by = filter_candidates(
        start,
        end,
        primes,
    )

    initial_candidates = int(
        np.count_nonzero(values >= 2)
    )

    if initial_candidates == 0 or not primes:
        return ()

    steps: list[FilterEfficiencyStep] = []
    candidates_before = initial_candidates

    for prime in primes:
        removed = int(
            np.count_nonzero(
                eliminated_by == prime
            )
        )

        candidates_after = (
            candidates_before - removed
        )

        marginal_removal_rate = (
            removed / candidates_before
            if candidates_before
            else 0.0
        )

        cumulative_survival_rate = (
            candidates_after / initial_candidates
        )

        steps.append(
            FilterEfficiencyStep(
                prime=prime,
                candidates_before=candidates_before,
                removed=removed,
                candidates_after=candidates_after,
                marginal_removal_rate=marginal_removal_rate,
                cumulative_survival_rate=cumulative_survival_rate,
            )
        )

        candidates_before = candidates_after

    assert candidates_before == int(
        np.count_nonzero(survives)
    )

    return tuple(steps)
