import pytest

from prime_lab.kinetic_sieve import (
    distinct_prime_factors,
    kinetic_sieve_event,
    kinetic_sieve_events,
    prime_trajectory,
)


def test_distinct_prime_factors_are_exact_and_ordered():
    assert distinct_prime_factors(0) == ()
    assert distinct_prime_factors(1) == ()
    assert distinct_prime_factors(2) == ()
    assert distinct_prime_factors(49) == (7,)
    assert distinct_prime_factors(60) == (2, 3, 5)
    assert distinct_prime_factors(2310) == (2, 3, 5, 7, 11)


def test_prime_event_has_no_eliminating_trajectory():
    event = kinetic_sieve_event(13)

    assert event.is_prime
    assert event.prime_factors == ()
    assert event.first_eliminating_prime is None
    assert not event.is_collision


def test_composite_event_preserves_first_eliminating_prime():
    event = kinetic_sieve_event(49)

    assert not event.is_prime
    assert event.prime_factors == (7,)
    assert event.first_eliminating_prime == 7
    assert not event.is_collision


def test_common_multiple_is_a_simultaneous_prime_collision():
    event = kinetic_sieve_event(30)

    assert not event.is_prime
    assert event.prime_factors == (2, 3, 5)
    assert event.first_eliminating_prime == 2
    assert event.is_collision


def test_prime_trajectories_visit_all_multiples_for_collision_view():
    assert prime_trajectory(
        2,
        12,
    ).landings == (
        2,
        4,
        6,
        8,
        10,
        12,
    )

    assert prime_trajectory(
        3,
        12,
        include_origin=False,
    ).landings == (
        6,
        9,
        12,
    )


def test_two_and_three_meet_exactly_at_common_multiples():
    two = set(
        prime_trajectory(2, 30).landings
    )
    three = set(
        prime_trajectory(3, 30).landings
    )

    assert sorted(two & three) == [
        6,
        12,
        18,
        24,
        30,
    ]


def test_event_interval_includes_neutral_prime_and_composite_states():
    events = kinetic_sieve_events(
        0,
        6,
    )

    assert [
        event.value
        for event in events
    ] == list(range(7))

    assert events[0].first_eliminating_prime is None
    assert events[1].first_eliminating_prime is None
    assert events[2].is_prime
    assert events[3].is_prime
    assert events[4].first_eliminating_prime == 2
    assert events[6].prime_factors == (2, 3)


def test_invalid_inputs_are_rejected():
    with pytest.raises(ValueError):
        distinct_prime_factors(-1)

    with pytest.raises(ValueError):
        kinetic_sieve_event(-1)

    with pytest.raises(ValueError):
        prime_trajectory(4, 20)

    with pytest.raises(ValueError):
        kinetic_sieve_events(10, 5)
