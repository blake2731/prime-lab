from ui.sieve_animation import build_sieve_animation


def test_animation_builds_wave_and_completion_frames():
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

    assert "prime_2_scan_1" in frame_names
    assert "prime_2_resolve_1" in frame_names
    assert "prime_2_complete" in frame_names

    assert "prime_3_scan_1" in frame_names
    assert "prime_3_complete" in frame_names

    assert frame_names[-1] == "prime_5_complete"

    assert len(frame_names) > 4


def test_animation_slider_stays_at_prime_checkpoints():
    figure = build_sieve_animation(
        1,
        30,
        (
            2,
            3,
            5,
        ),
    )

    assert len(figure.layout.sliders) == 1

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
