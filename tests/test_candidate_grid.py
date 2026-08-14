import numpy as np
import pytest

from prime_lab.filters import filter_candidates
from ui.candidate_grid import LABEL_LIMIT, build_candidate_figure


def test_candidate_grid_uses_explicit_width():
    values, survives, eliminated_by = filter_candidates(
        1,
        30,
        (2, 3, 5),
    )

    figure = build_candidate_figure(
        values,
        survives,
        eliminated_by,
        None,
        grid_width=7,
    )

    heatmap = figure.data[0]
    assert np.asarray(heatmap.z).shape == (5, 7)


def test_candidate_grid_labels_small_fields_directly():
    values, survives, eliminated_by = filter_candidates(1, 30, (2, 3, 5))

    figure = build_candidate_figure(
        values,
        survives,
        eliminated_by,
        5,
        grid_width=10,
    )

    text_traces = [trace for trace in figure.data if trace.type == "scatter" and trace.mode == "text"]
    assert len(text_traces) == 1
    assert list(text_traces[0].text[:5]) == ["1", "2", "3", "4", "5"]


def test_candidate_grid_omits_direct_labels_for_dense_fields():
    values, survives, eliminated_by = filter_candidates(1, LABEL_LIMIT + 1, (2, 3, 5))

    figure = build_candidate_figure(
        values,
        survives,
        eliminated_by,
        5,
    )

    assert not any(
        trace.type == "scatter" and trace.mode == "text"
        for trace in figure.data
    )


def test_candidate_grid_rejects_invalid_width():
    values, survives, eliminated_by = filter_candidates(1, 10, ())

    with pytest.raises(ValueError, match="grid_width must be at least 1"):
        build_candidate_figure(
            values,
            survives,
            eliminated_by,
            None,
            grid_width=0,
        )
