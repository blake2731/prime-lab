import numpy as np
import pytest

from prime_lab.filters import filter_candidates


def test_numbers_below_two_do_not_survive():
    values, survives, _ = filter_candidates(
        1,
        5,
        (),
    )

    assert values.tolist() == [1, 2, 3, 4, 5]
    assert survives.tolist() == [
        False,
        True,
        True,
        True,
        True,
    ]


def test_filter_two_removes_even_composites():
    values, survives, eliminated_by = filter_candidates(
        1,
        10,
        (2,),
    )

    surviving_values = values[survives]

    assert surviving_values.tolist() == [
        2,
        3,
        5,
        7,
        9,
    ]

    assert eliminated_by[3] == 2
    assert eliminated_by[5] == 2
    assert eliminated_by[7] == 2
    assert eliminated_by[9] == 2


def test_multiple_filters_leave_expected_candidates():
    values, survives, eliminated_by = filter_candidates(
        1,
        30,
        (2, 3, 5),
    )

    surviving_values = values[survives]

    assert surviving_values.tolist() == [
        2,
        3,
        5,
        7,
        11,
        13,
        17,
        19,
        23,
        29,
    ]

    assert eliminated_by[8] == 3
    assert eliminated_by[24] == 5


def test_prime_is_not_eliminated_by_itself():
    values, survives, eliminated_by = filter_candidates(
        2,
        7,
        (2, 3, 5, 7),
    )

    for prime in (2, 3, 5, 7):
        index = np.where(values == prime)[0][0]

        assert survives[index]
        assert eliminated_by[index] == 0


def test_invalid_range_raises_error():
    with pytest.raises(ValueError):
        filter_candidates(
            10,
            1,
            (2, 3, 5),
        )
