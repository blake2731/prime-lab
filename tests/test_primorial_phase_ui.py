from prime_lab.primorial_phase import (
    density_convergence_sweep,
    prime_density_observation,
    primorial_stages,
    survivor_residues,
)
from ui.primorial_phase import (
    UNRESOLVED_CANDIDATE,
    build_asymptotic_residual_figure,
    build_density_comparison_figure,
    build_density_residual_figure,
    build_primorial_wheel_figure,
    build_survivor_fraction_figure,
)


def test_survivor_fraction_figure_compares_exact_and_mertens_curves():
    figure = build_survivor_fraction_figure(primorial_stages(6))

    assert len(figure.data) == 2
    assert figure.data[0].name == "Exact survivor fraction"
    assert figure.data[1].name == "Mertens approximation"
    assert figure.data[0].line.color == UNRESOLVED_CANDIDATE


def test_primorial_wheel_marks_modulo_30_survivors():
    modulus, survivors = survivor_residues((2, 3, 5))
    figure = build_primorial_wheel_figure(
        modulus=modulus,
        survivor_residues=survivors,
        cutoff_prime=5,
    )

    assert len(figure.data) == 2
    assert figure.data[1].name == "Avoids phase zero"
    assert len(figure.data[1].x) == 8
    assert list(figure.data[1].customdata) == list(survivors)
    assert "P = 30" in figure.layout.annotations[0].text


def test_density_comparison_figure_contains_four_distinct_quantities():
    observation = prime_density_observation(1_000)
    figure = build_density_comparison_figure(observation)

    assert len(figure.data) == 1
    assert len(figure.data[0].x) == 4
    labels = list(figure.data[0].x)
    assert "Primorial survivor fraction" in labels
    assert "Observed π(x) / x" in labels
    assert "Prime number theorem 1 / ln(x)" in labels


def test_density_residual_figure_contains_two_signed_error_series():
    points = density_convergence_sweep(2, 4)
    figure = build_density_residual_figure(points)

    assert len(figure.data) == 2
    assert figure.data[0].name == "π(x)/x − 1/ln(x)"
    assert figure.data[1].name == "Primorial survivor − π(x)/x"
    assert list(figure.data[0].x) == [100, 1_000, 10_000]
    assert figure.layout.xaxis.type == "log"


def test_asymptotic_residual_figure_tracks_two_classical_references():
    points = density_convergence_sweep(2, 4)
    figure = build_asymptotic_residual_figure(points)

    assert len(figure.data) == 2
    assert figure.data[0].name == "Survivor/PNT ratio − 2e^(−γ)"
    assert figure.data[1].name == "Exact survivor − Mertens estimate"
    assert figure.layout.xaxis.type == "log"
