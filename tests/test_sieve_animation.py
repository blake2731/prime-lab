import numpy as np

from prime_lab.certification import confirmed_prime_mask
from prime_lab.filters import filter_candidates
from ui.sieve_animation import build_sieve_animation


def test_animation_uses_impact_and_settle_frames_with_prime_checkpoints():
    figure = build_sieve_animation(
        1,
        30,
        (2, 3, 5),
    )

    frame_names = [frame.name for frame in figure.frames]
    assert frame_names[0] == "start"

    for prime in (2, 3, 5):
        assert f"prime_{prime}_impact" in frame_names
        assert f"prime_{prime}_settle" in frame_names

    slider = figure.layout.sliders[0]
    assert slider.active == 0
    assert [step.label for step in slider.steps] == ["Start", "2", "3", "5"]

    button_labels = [button.label for button in figure.layout.updatemenus[0].buttons]
    assert button_labels == ["▶ Play sieve", "❚❚ Pause", "↺ Start"]


def test_stage_playback_frame_sequence_is_deterministic():
    first = build_sieve_animation(1, 100, (2, 3, 5, 7))
    second = build_sieve_animation(1, 100, (2, 3, 5, 7))

    assert [frame.name for frame in first.frames] == [
        frame.name for frame in second.frames
    ]


def test_sieve_animation_preserves_explicit_projection_width():
    figure = build_sieve_animation(
        1,
        30,
        (2, 3, 5),
        grid_width=7,
    )

    start_heatmap = figure.data[0]
    prime_5_settle = next(
        frame for frame in figure.frames if frame.name == "prime_5_settle"
    )
    final_heatmap = prime_5_settle.data[0]

    assert np.asarray(start_heatmap.z).shape == (5, 7)
    assert np.asarray(final_heatmap.z).shape == (5, 7)


def test_impact_highlights_only_newly_resolved_composites():
    figure = build_sieve_animation(1, 30, (2, 3, 5))

    previous_values, previous_survives, _ = filter_candidates(1, 30, (2, 3))
    _, stage_survives, _ = filter_candidates(1, 30, (2, 3, 5))
    expected_new = int(np.count_nonzero(previous_survives & ~stage_survives))

    impact = next(
        frame for frame in figure.frames if frame.name == "prime_5_impact"
    )
    impact_status = np.asarray(impact.data[0].z)

    assert int(np.count_nonzero(impact_status == 2)) == expected_new


def test_settled_checkpoint_turns_resolved_composites_gray_and_keeps_confirmed_teal():
    primes = (2, 3, 5)
    figure = build_sieve_animation(1, 30, primes)

    values, survives, eliminated_by = filter_candidates(1, 30, primes)
    confirmed = confirmed_prime_mask(values, survives, primes)

    settled = next(
        frame for frame in figure.frames if frame.name == "prime_5_settle"
    )
    settled_status = np.asarray(settled.data[0].z)

    assert int(np.count_nonzero(settled_status == 2)) == 0
    assert int(np.count_nonzero(settled_status == 3)) == int(
        np.count_nonzero(confirmed)
    )
    assert int(np.count_nonzero(settled_status == 0)) >= int(
        np.count_nonzero(eliminated_by > 0)
    )
