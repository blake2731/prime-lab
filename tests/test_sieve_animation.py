from ui.sieve_animation import build_sieve_animation


def test_animation_has_expected_filter_frames():
    figure = build_sieve_animation(
        1,
        30,
        (
            2,
            3,
            5,
        ),
    )

    frame_names = [frame.name for frame in figure.frames]

    assert frame_names == [
        "start",
        "prime_2",
        "prime_3",
        "prime_5",
    ]

    assert len(figure.layout.sliders) == 1

    assert figure.layout.sliders[0].active == 3
