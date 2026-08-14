from dataclasses import dataclass
from math import gcd

import numpy as np


@dataclass(frozen=True)
class ResidueClassSummary:
    """Counts for one residue class in the current experiment state."""

    residue: int
    prime_eligible: bool
    confirmed: int
    unresolved: int
    current_removed: int



def residue_class_summaries(
    values: np.ndarray,
    survives: np.ndarray,
    eliminated_by: np.ndarray,
    confirmed: np.ndarray,
    active_prime: int | None,
    modulus: int = 30,
) -> tuple[ResidueClassSummary, ...]:
    """Summarize the current candidate state by residue class."""

    if modulus < 2:
        raise ValueError("modulus must be at least 2")

    shapes = {
        values.shape,
        survives.shape,
        eliminated_by.shape,
        confirmed.shape,
    }

    if len(shapes) != 1:
        raise ValueError(
            "values, survives, eliminated_by, and confirmed must have matching shapes"
        )

    residues = values % modulus

    summaries: list[ResidueClassSummary] = []

    for residue in range(modulus):
        residue_mask = residues == residue

        confirmed_count = int(
            np.count_nonzero(
                residue_mask
                & confirmed
            )
        )

        unresolved_count = int(
            np.count_nonzero(
                residue_mask
                & survives
                & ~confirmed
            )
        )

        if active_prime is None:
            current_removed_count = 0

        else:
            current_removed_count = int(
                np.count_nonzero(
                    residue_mask
                    & (eliminated_by == active_prime)
                )
            )

        summaries.append(
            ResidueClassSummary(
                residue=residue,
                prime_eligible=(
                    gcd(residue, modulus) == 1
                ),
                confirmed=confirmed_count,
                unresolved=unresolved_count,
                current_removed=current_removed_count,
            )
        )

    return tuple(summaries)
