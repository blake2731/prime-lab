import pytest

from prime_lab.filter_efficiency import (
    filter_efficiency_steps,
)
from ui.filter_efficiency import (
    build_filter_efficiency_figure,
)


def test_filter_efficiency_tracks_unique_work():
    steps = filter_efficiency_steps(
        1,
        30,
        (
            2,
            3,
            5,
        ),
    )

    assert [
        step.prime
        for step in steps
    ] == [
        2,
        3,
        5,
    ]

    assert [
        step.removed
        for step in steps
    ] == [
        14,
        4,
        1,
    ]

    assert [
        step.candidates_after
        for step in steps
    ] == [
        15,
        11,
        10,
    ]

    assert steps[0].marginal_removal_rate == pytest.approx(
        14 / 29
    )
    assert steps[1].marginal_removal_rate == pytest.approx(
        4 / 15
    )
    assert steps[2].marginal_removal_rate == pytest.approx(
        1 / 11
    )

    assert steps[-1].cumulative_survival_rate == pytest.approx(
        10 / 29
    )


def test_filter_efficiency_figure_matches_analysis():
    figure = build_filter_efficiency_figure(
        1,
        30,
        (
            2,
            3,
            5,
        ),
    )

    removal_bars = figure.data[0]
    marginal_line = figure.data[1]

    assert list(removal_bars.x) == [
        2,
        3,
        5,
    ]

    assert list(removal_bars.y) == [
        14,
        4,
        1,
    ]

    assert marginal_line.y[-1] == pytest.approx(
        (1 / 11) * 100.0
    )


def test_filter_efficiency_is_empty_without_filters():
    assert filter_efficiency_steps(
        1,
        30,
        (),
    ) == ()
