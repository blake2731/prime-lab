import numpy as np

from prime_lab.certification import confirmed_prime_mask
from prime_lab.filters import filter_candidates
from ui.residue_structure import (
    PRIME_ELIGIBLE_RESIDUES,
    build_residue_figure,
)


def test_modulo_30_prime_eligible_residues():
    assert PRIME_ELIGIBLE_RESIDUES == (
        1,
        7,
        11,
        13,
        17,
        19,
        23,
        29,
    )


def test_residue_figure_maps_60_values_into_30_rows():
    values, survives, eliminated_by = filter_candidates(
        1,
        60,
        (
            2,
            3,
            5,
        ),
    )

    confirmed = confirmed_prime_mask(
        values,
        survives,
        (
            2,
            3,
            5,
        ),
    )

    figure = build_residue_figure(
        values,
        survives,
        eliminated_by,
        confirmed,
        5,
    )

    heatmap = figure.data[0]
    unresolved_bar = figure.data[1]
    confirmed_bar = figure.data[2]

    assert np.asarray(heatmap.z).shape == (
        30,
        3,
    )

    assert int(
        np.sum(unresolved_bar.x)
    ) == 2

    assert int(
        np.sum(confirmed_bar.x)
    ) == 15
