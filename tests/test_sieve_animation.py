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
