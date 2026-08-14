import pytest

from prime_lab.prime_shadows import (
    CONFIRMED_CODE,
    TARGET_CODE,
    PrimeShadow,
    build_prime_shadow,
    find_shadow_matches,
    shadow_similarity,
    shadow_state_counts,
)


def test_prime_shadow_encodes_exact_local_sieve_environment():
    shadow = build_prime_shadow(
        center_prime=11,
        radius=5,
        filter_primes=(
            2,
            3,
            5,
        ),
    )

    assert shadow.values == (
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
    )

    assert shadow.state_codes == (
        2,
        CONFIRMED_CODE,
        2,
        3,
        2,
        TARGET_CODE,
        2,
        CONFIRMED_CODE,
        2,
        3,
        2,
    )

    counts = shadow_state_counts(
        shadow
    )

    assert counts == {
        "filtered_composites": 8,
        "confirmed_neighbors": 2,
        "unresolved_neighbors": 0,
        "higher_prime_shadows": 0,
    }


def test_shadow_rejects_unconfirmed_center():
    with pytest.raises(
        ValueError,
        match="must be confirmed",
    ):
        build_prime_shadow(
            center_prime=29,
            radius=5,
            filter_primes=(
                2,
                3,
            ),
        )


def test_shadow_similarity_can_remove_base_wheel_effects():
    first = PrimeShadow(
        center_prime=101,
        radius=2,
        offsets=(-2, -1, 0, 1, 2),
        values=(99, 100, 101, 102, 103),
        state_codes=(
            2,
            7,
            TARGET_CODE,
            CONFIRMED_CODE,
            11,
        ),
    )

    second = PrimeShadow(
        center_prime=1009,
        radius=2,
        offsets=(-2, -1, 0, 1, 2),
        values=(1007, 1008, 1009, 1010, 1011),
        state_codes=(
            2,
            7,
            TARGET_CODE,
            CONFIRMED_CODE,
            13,
        ),
    )

    full_similarity, full_positions = shadow_similarity(
        first,
        second,
    )

    deep_similarity, deep_positions = shadow_similarity(
        first,
        second,
        ignore_eliminators=(
            2,
            3,
            5,
        ),
    )

    assert full_positions == 4
    assert full_similarity == pytest.approx(
        0.75
    )

    assert deep_positions == 3
    assert deep_similarity == pytest.approx(
        2 / 3
    )


def test_similarity_search_excludes_target_and_is_ranked():
    matches = find_shadow_matches(
        target_prime=101,
        candidate_primes=(
            101,
            103,
            107,
            109,
            113,
        ),
        radius=5,
        filter_primes=(
            2,
            3,
            5,
            7,
            11,
        ),
    )

    assert len(matches) == 4
    assert all(
        match.prime != 101
        for match in matches
    )

    ranking = [
        (
            match.deep_similarity,
            match.full_similarity,
        )
        for match in matches
    ]

    assert ranking == sorted(
        ranking,
        reverse=True,
    )
