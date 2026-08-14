import numpy as np

from prime_lab.certification import confirmed_prime_mask
from prime_lab.filters import filter_candidates
from ui.sieve_animation import build_sieve_animation


def test_animation_uses_scattered_drop_frames_and_prime_checkpoints():
    figure = build_sieve_animation(
        1,
        30,
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

    for prime in (2, 3, 5):
        assert any(
            name.startswith(
                f"prime_{prime}_drop_"
            )
            for name in frame_names
        )

        assert (
            f"prime_{prime}_settle"
            in frame_names
        )

    slider = figure.layout.sliders[0]

    assert slider.active == 3

    labels = [
        step.label
        for step in slider.steps
    ]

    assert labels == [
        "Start",
        "2",
        "3",
        "5",
    ]


def test_rainfall_frame_sequence_is_deterministic():
    first = build_sieve_animation(
        1,
        100,
        (
            2,
            3,
            5,
            7,
        ),
    )

    second = build_sieve_animation(
        1,
        100,
        (
            2,
            3,
            5,
            7,
        ),
    )

    first_names = [
        frame.name
        for frame in first.frames
    ]

    second_names = [
        frame.name
        for frame in second.frames
    ]

    assert first_names == second_names


def test_sieve_animation_preserves_explicit_projection_width():
    figure = build_sieve_animation(
        1,
        30,
        (
            2,
            3,
            5,
        ),
        grid_width=7,
    )

    final_heatmap = figure.data[0]
    start_heatmap = figure.frames[0].data[0]

    assert np.asarray(final_heatmap.z).shape == (
        5,
        7,
    )

    assert np.asarray(start_heatmap.z).shape == (
        5,
        7,
    )


def test_settled_checkpoint_keeps_current_filter_eliminations_amber():
    primes = (
        2,
        3,
        5,
    )

    figure = build_sieve_animation(
        1,
        30,
        primes,
    )

    values, survives, eliminated_by = filter_candidates(
        1,
        30,
        primes,
    )

    confirmed = confirmed_prime_mask(
        values,
        survives,
        primes,
    )

    final_status = np.asarray(
        figure.data[0].z
    )

    assert int(
        np.count_nonzero(
            final_status == 2
        )
    ) == int(
        np.count_nonzero(
            eliminated_by == 5
        )
    )

    assert int(
        np.count_nonzero(
            final_status == 3
        )
    ) == int(
        np.count_nonzero(
            confirmed
        )
    )

    prime_3_frame = next(
        frame
        for frame in figure.frames
        if frame.name == "prime_3_settle"
    )

    stage_values, stage_survives, stage_eliminated_by = filter_candidates(
        1,
        30,
        (
            2,
            3,
        ),
    )

    stage_confirmed = confirmed_prime_mask(
        stage_values,
        stage_survives,
        (
            2,
            3,
        ),
    )

    prime_3_status = np.asarray(
        prime_3_frame.data[0].z
    )

    assert int(
        np.count_nonzero(
            prime_3_status == 2
        )
    ) == int(
        np.count_nonzero(
            stage_eliminated_by == 3
        )
    )

    assert int(
        np.count_nonzero(
            prime_3_status == 3
        )
    ) == int(
        np.count_nonzero(
            stage_confirmed
        )
    )
