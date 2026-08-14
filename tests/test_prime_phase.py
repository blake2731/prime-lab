from math import isclose, pi

import pytest

from prime_lab.prime_phase import (
    circular_phase_distance,
    is_prime_from_relevant_phases,
    joint_phase_cycle,
    phase_signature_distance,
    phase_state,
    phase_states,
    primes_up_to,
    relevant_divisor_primes,
    synchronized_primes,
)


def test_phase_state_normalizes_modular_remainder_to_one_turn():
    state = phase_state(5, 3)

    assert state.remainder == 2
    assert isclose(state.phase_fraction, 2 / 3)
    assert isclose(state.angle_radians, 4 * pi / 3)
    assert isclose(state.angle_degrees, 240.0)
    assert not state.is_zero_crossing


def test_phase_zero_means_exact_multiple_but_self_is_not_composite_evidence():
    self_state = phase_state(5, 5)
    divisor_state = phase_state(49, 7)

    assert self_state.is_zero_crossing
    assert not self_state.is_relevant_divisor
    assert divisor_state.is_zero_crossing
    assert divisor_state.is_relevant_divisor


def test_relevant_phase_zero_cycles_classify_primes_and_composites():
    assert relevant_divisor_primes(29) == ()
    assert relevant_divisor_primes(30) == (2, 3, 5)
    assert relevant_divisor_primes(49) == (7,)

    assert is_prime_from_relevant_phases(29)
    assert not is_prime_from_relevant_phases(30)
    assert not is_prime_from_relevant_phases(49)


def test_selected_synchronization_reports_shared_prime_cycles():
    assert synchronized_primes(30, [2, 3, 5, 7]) == (2, 3, 5)
    assert synchronized_primes(31, [2, 3, 5, 7]) == ()


def test_joint_phase_cycle_visits_every_residue_pair_once():
    points = joint_phase_cycle(3, 5)

    assert len(points) == 15
    pairs = {(point.first_remainder, point.second_remainder) for point in points}
    assert len(pairs) == 15

    shared = [point for point in points if point.first_zero and point.second_zero]
    assert [point.integer for point in shared] == [0]


def test_joint_phase_cycle_rejects_invalid_pairs():
    with pytest.raises(ValueError):
        joint_phase_cycle(3, 3)

    with pytest.raises(ValueError):
        joint_phase_cycle(4, 5)


def test_phase_signature_repeats_after_joint_period():
    primes = (2, 3, 5)

    assert isclose(phase_signature_distance(17, 47, primes), 0.0)
    assert circular_phase_distance(0.95, 0.05) == pytest.approx(0.10)


def test_prime_collection_and_duplicate_validation():
    assert primes_up_to(13) == (2, 3, 5, 7, 11, 13)

    with pytest.raises(ValueError):
        phase_states(10, [2, 2, 3])

    with pytest.raises(ValueError):
        phase_state(10, 4)
