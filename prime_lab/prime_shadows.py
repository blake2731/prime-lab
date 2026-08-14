from dataclasses import dataclass
from collections.abc import Sequence

import numpy as np

from prime_lab.certification import confirmed_prime_mask
from prime_lab.filters import filter_candidates


TARGET_CODE = -3
CONFIRMED_CODE = -2
UNRESOLVED_CODE = -1
NON_CANDIDATE_CODE = 0


@dataclass(frozen=True)
class PrimeShadow:
    """Local sieve environment centered on one confirmed prime."""

    center_prime: int
    radius: int
    offsets: tuple[int, ...]
    values: tuple[int, ...]
    state_codes: tuple[int, ...]


@dataclass(frozen=True)
class ShadowMatch:
    """Similarity between one target shadow and another prime shadow."""

    prime: int
    distance: int
    residue_mod_30: int
    full_similarity: float
    deep_similarity: float
    deep_positions_compared: int


def build_prime_shadow(
    center_prime: int,
    radius: int,
    filter_primes: Sequence[int],
) -> PrimeShadow:
    """Encode which applied prime first resolves each nearby integer."""

    if radius < 1:
        raise ValueError("radius must be at least 1")

    start = center_prime - radius
    end = center_prime + radius

    if start < 1:
        raise ValueError(
            "shadow window must stay at or above 1"
        )

    primes = tuple(filter_primes)

    values, survives, eliminated_by = filter_candidates(
        start,
        end,
        primes,
    )

    confirmed = confirmed_prime_mask(
        values,
        survives,
        primes,
    )

    center_index = radius

    if int(values[center_index]) != center_prime:
        raise AssertionError(
            "shadow center does not align with center_prime"
        )

    if not bool(confirmed[center_index]):
        raise ValueError(
            "center_prime must be confirmed by the selected filter sequence"
        )

    offsets = tuple(
        range(-radius, radius + 1)
    )

    state_codes: list[int] = []

    for index, value in enumerate(values):
        if index == center_index:
            code = TARGET_CODE

        elif confirmed[index]:
            code = CONFIRMED_CODE

        elif survives[index]:
            code = UNRESOLVED_CODE

        elif eliminated_by[index] > 0:
            code = int(eliminated_by[index])

        else:
            code = NON_CANDIDATE_CODE

        state_codes.append(code)

    return PrimeShadow(
        center_prime=int(center_prime),
        radius=int(radius),
        offsets=offsets,
        values=tuple(
            int(value)
            for value in values
        ),
        state_codes=tuple(state_codes),
    )


def shadow_similarity(
    first: PrimeShadow,
    second: PrimeShadow,
    ignore_eliminators: Sequence[int] = (),
) -> tuple[float, int]:
    """Compare two shadows position by position using exact state identity."""

    if first.offsets != second.offsets:
        raise ValueError(
            "prime shadows must use matching offsets"
        )

    ignored = set(
        int(value)
        for value in ignore_eliminators
    )

    matches = 0
    compared = 0

    for offset, first_code, second_code in zip(
        first.offsets,
        first.state_codes,
        second.state_codes,
        strict=True,
    ):
        if offset == 0:
            continue

        if (
            first_code == NON_CANDIDATE_CODE
            or second_code == NON_CANDIDATE_CODE
        ):
            continue

        if (
            first_code in ignored
            or second_code in ignored
        ):
            continue

        compared += 1

        if first_code == second_code:
            matches += 1

    if compared == 0:
        return 0.0, 0

    return matches / compared, compared


def find_shadow_matches(
    target_prime: int,
    candidate_primes: Sequence[int],
    radius: int,
    filter_primes: Sequence[int],
    deep_ignore: Sequence[int] = (2, 3, 5),
) -> tuple[ShadowMatch, ...]:
    """Rank confirmed primes by local sieve environment similarity."""

    target_shadow = build_prime_shadow(
        target_prime,
        radius,
        filter_primes,
    )

    matches: list[ShadowMatch] = []

    for candidate_prime in candidate_primes:
        candidate = int(candidate_prime)

        if candidate == target_prime:
            continue

        candidate_shadow = build_prime_shadow(
            candidate,
            radius,
            filter_primes,
        )

        full_similarity, _ = shadow_similarity(
            target_shadow,
            candidate_shadow,
        )

        deep_similarity, deep_positions = shadow_similarity(
            target_shadow,
            candidate_shadow,
            ignore_eliminators=deep_ignore,
        )

        matches.append(
            ShadowMatch(
                prime=candidate,
                distance=abs(candidate - target_prime),
                residue_mod_30=candidate % 30,
                full_similarity=full_similarity,
                deep_similarity=deep_similarity,
                deep_positions_compared=deep_positions,
            )
        )

    return tuple(
        sorted(
            matches,
            key=lambda match: (
                -match.deep_similarity,
                -match.full_similarity,
                match.distance,
                match.prime,
            ),
        )
    )


def shadow_state_counts(
    shadow: PrimeShadow,
) -> dict[str, int]:
    """Summarize the local environment around one center prime."""

    codes = shadow.state_codes

    return {
        "filtered_composites": sum(
            code > 0
            for code in codes
        ),
        "confirmed_neighbors": sum(
            code == CONFIRMED_CODE
            for code in codes
        ),
        "unresolved_neighbors": sum(
            code == UNRESOLVED_CODE
            for code in codes
        ),
        "higher_prime_shadows": sum(
            code > 5
            for code in codes
        ),
    }
