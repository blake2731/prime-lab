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

    frame_names = [
        frame.name
        for frame in figure.frames
    ]

    assert frame_names == [
        "start",
        "prime_2_hit",
        "prime_2_settle",
        "prime_3_hit",
        "prime_3_settle",
        "prime_5_hit",
    ]

    assert len(figure.layout.sliders) == 1

    assert figure.layout.sliders[0].active == 3

    slider_labels = [
        step.label
        for step in figure.layout.sliders[0].steps
    ]

    assert slider_labels == [
        "Start",
        "2",
        "3",
        "5",
    ]


def test_final_selected_filter_remains_visible():
    figure = build_sieve_animation(
        1,
        30,
        (
            2,
            3,
            5,
        ),
    )

    assert figure.frames[-1].name == "prime_5_hit"
