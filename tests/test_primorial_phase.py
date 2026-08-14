from math import isclose

import pytest

from prime_lab.primorial_phase import (
    EULER_MASCHERONI,
    density_convergence_sweep,
    prime_count_up_to,
    prime_density_observation,
    primorial_stages,
    survivor_residues,
)


def test_early_primorial_stages_match_exact_totient_counts():
    stages = primorial_stages(4)

    assert [stage.prime for stage in stages] == [2, 3, 5, 7]
    assert [stage.primorial for stage in stages] == [2, 6, 30, 210]
    assert [stage.surviving_states for stage in stages] == [1, 2, 8, 48]
    assert stages[0].survivor_fraction == pytest.approx(1 / 2)
    assert stages[1].survivor_fraction == pytest.approx(1 / 3)
    assert stages[2].survivor_fraction == pytest.approx(8 / 30)
    assert stages[3].survivor_fraction == pytest.approx(48 / 210)


def test_survivor_fraction_is_product_of_one_minus_inverse_primes():
    stages = primorial_stages(6)
    running = 1.0

    for stage in stages:
        running *= (stage.prime - 1) / stage.prime
        assert stage.survivor_fraction == pytest.approx(running)
        assert stage.eliminated_fraction == pytest.approx(1.0 - running)


def test_modulo_30_survivors_are_the_prime_eligible_residues():
    modulus, survivors = survivor_residues((2, 3, 5))

    assert modulus == 30
    assert survivors == (1, 7, 11, 13, 17, 19, 23, 29)


def test_survivor_residue_validation_and_visualization_limit():
    with pytest.raises(ValueError):
        survivor_residues(())

    with pytest.raises(ValueError):
        survivor_residues((2, 2, 3))

    with pytest.raises(ValueError):
        survivor_residues((2, 3, 4))

    with pytest.raises(ValueError):
        survivor_residues((2, 3, 5, 7, 11, 13, 17))


def test_prime_counting_sieve_returns_known_pi_values():
    assert prime_count_up_to(10) == 4
    assert prime_count_up_to(100) == 25
    assert prime_count_up_to(1_000) == 168


def test_density_observation_separates_wheel_and_prime_density():
    observation = prime_density_observation(100)

    assert observation.prime_count == 25
    assert observation.empirical_prime_density == pytest.approx(0.25)
    assert observation.proof_limit == 10
    assert observation.proof_prime_count == 4
    assert observation.proof_cutoff_prime == 7
    assert observation.wheel_survivor_fraction == pytest.approx(48 / 210)
    assert observation.pnt_density > 0
    assert observation.mertens_at_proof_cutoff > 0
    assert observation.wheel_to_pnt_ratio > 0
    assert observation.expected_sqrt_ratio == pytest.approx(
        2.0 * 2.718281828459045 ** (-EULER_MASCHERONI),
        rel=1e-12,
    )


def test_mertens_approximation_decreases_across_early_stages():
    stages = primorial_stages(10)
    estimates = [stage.mertens_estimate for stage in stages]

    assert all(
        first > second
        for first, second in zip(estimates[:-1], estimates[1:], strict=True)
    )
    assert all(stage.survivor_to_mertens_ratio > 0 for stage in stages)


def test_density_convergence_sweep_uses_known_prime_counts():
    points = density_convergence_sweep(2, 4)

    assert [point.maximum_integer for point in points] == [100, 1_000, 10_000]
    assert [point.prime_count for point in points] == [25, 168, 1_229]


def test_density_convergence_residuals_match_their_definitions():
    point = density_convergence_sweep(2, 2)[0]
    expected_ratio = 2.0 * 2.718281828459045 ** (-EULER_MASCHERONI)

    assert point.prime_density_minus_pnt == pytest.approx(
        point.empirical_prime_density - point.pnt_density
    )
    assert point.wheel_minus_prime_density == pytest.approx(
        point.wheel_survivor_fraction - point.empirical_prime_density
    )
    assert point.wheel_to_pnt_ratio == pytest.approx(
        point.wheel_survivor_fraction / point.pnt_density
    )
    assert point.wheel_ratio_error == pytest.approx(
        point.wheel_to_pnt_ratio - expected_ratio
    )
    assert point.mertens_absolute_error == pytest.approx(
        point.wheel_survivor_fraction - point.mertens_estimate
    )
    assert point.mertens_relative_error == pytest.approx(
        point.mertens_absolute_error / point.mertens_estimate
    )


def test_invalid_stage_density_and_sweep_inputs_are_rejected():
    with pytest.raises(ValueError):
        primorial_stages(0)

    with pytest.raises(ValueError):
        prime_density_observation(9)

    with pytest.raises(ValueError):
        density_convergence_sweep(1, 4)

    with pytest.raises(ValueError):
        density_convergence_sweep(5, 4)

    with pytest.raises(ValueError):
        density_convergence_sweep(2, 8)
