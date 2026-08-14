import numpy as np

from prime_lab.filters import filter_candidates
from ui.residue_animation import build_residue_animation


def test_residue_animation_uses_prime_checkpoints():
    figure = build_residue_animation(
        1,
        60,
        (
            2,
            3,
            5,
        ),
    )

    frame_names = [
        frame.name
        for frame in figure.frames
    ]

    assert frame_names[0] == "start"
    assert "prime_2_settle" in frame_names
    assert "prime_3_settle" in frame_names
    assert frame_names[-1] == "prime_5_settle"
    assert len(frame_names) > 4

    slider = figure.layout.sliders[0]

    assert [
        step.label
        for step in slider.steps
    ] == [
        "Start",
        "2",
        "3",
        "5",
    ]

    assert slider.active == 3


def test_residue_animation_settles_to_exact_prime_5_state():
    figure = build_residue_animation(
        1,
        60,
        (
            2,
            3,
            5,
        ),
    )

    final_frame = figure.frames[-1]
    unresolved_bar = final_frame.data[1]
    confirmed_bar = final_frame.data[2]

    assert int(
        np.sum(unresolved_bar.x)
    ) == 3

    assert int(
        np.sum(confirmed_bar.x)
    ) == 15

    unresolved_residues = {
        residue
        for residue, count in enumerate(
            unresolved_bar.x
        )
        if count
    }

    assert unresolved_residues == {
        19,
        23,
        29,
    }


def test_residue_checkpoint_keeps_current_filter_eliminations_amber():
    primes = (
        2,
        3,
        5,
    )

    figure = build_residue_animation(
        1,
        60,
        primes,
    )

    _, _, eliminated_by = filter_candidates(
        1,
        60,
        primes,
    )

    expected_current = int(
        np.count_nonzero(
            eliminated_by == 5
        )
    )

    final_status = np.asarray(
        figure.data[0].z
    )

    final_frame_status = np.asarray(
        figure.frames[-1].data[0].z
    )

    assert int(
        np.count_nonzero(
            final_status == 2
        )
    ) == expected_current

    assert int(
        np.count_nonzero(
            final_frame_status == 2
        )
    ) == expected_current
