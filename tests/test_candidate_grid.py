import numpy as np
import pytest

from prime_lab.filters import filter_candidates
from ui.candidate_grid import build_candidate_figure


def test_candidate_grid_uses_explicit_width():
    values, survives, eliminated_by = filter_candidates(
        1,
        30,
        (
            2,
            3,
            5,
        ),
    )

    figure = build_candidate_figure(
        values,
        survives,
        eliminated_by,
        None,
        grid_width=7,
    )

    heatmap = figure.data[0]

    assert np.asarray(heatmap.z).shape == (
        5,
        7,
    )


def test_candidate_grid_rejects_invalid_width():
    values, survives, eliminated_by = filter_candidates(
        1,
        10,
        (),
    )

    with pytest.raises(
        ValueError,
        match="grid_width must be at least 1",
    ):
        build_candidate_figure(
            values,
            survives,
            eliminated_by,
            None,
            grid_width=0,
        )
