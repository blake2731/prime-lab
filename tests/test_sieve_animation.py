import numpy as np

from prime_lab.certification import confirmed_prime_mask
from prime_lab.filters import filter_candidates
from ui.candidate_grid import CONFIRMED_PRIME, NEWLY_RESOLVED
from ui.sieve_animation import build_sieve_animation


def test_animation_uses_focus_cascade_certification_and_settle_stages():
    figure = build_sieve_animation(1, 30, (2, 3, 5))
    frame_names = [frame.name for frame in figure.frames]

    assert frame_names[0] == "start"
    for prime in (2, 3, 5):
        assert f"prime_{prime}_focus" in frame_names
        assert any(name.startswith(f"prime_{prime}_cascade_") for name in frame_names)
        assert f"prime_{prime}_settle" in frame_names

    assert any(name.startswith("prime_5_certify_") for name in frame_names)
    assert [step.label for step in figure.layout.sliders[0].steps] == ["Start", "2", "3", "5"]
    assert [button.label for button in figure.layout.updatemenus[0].buttons] == [
        "▶ Play cascade",
        "❚❚ Pause",
        "◫ Reduced motion",
        "↺ Start",
    ]


def test_stage_playback_frame_sequence_is_deterministic():
    first = build_sieve_animation(1, 100, (2, 3, 5, 7))
    second = build_sieve_animation(1, 100, (2, 3, 5, 7))
    assert [frame.name for frame in first.frames] == [frame.name for frame in second.frames]


def test_every_integer_keeps_the_same_position_across_all_frames():
    figure = build_sieve_animation(1, 100, (2, 3, 5, 7))
    base_x = np.asarray(figure.data[0].x)
    base_y = np.asarray(figure.data[0].y)

    for frame in figure.frames:
        assert np.array_equal(np.asarray(frame.data[0].x), base_x)
        assert np.array_equal(np.asarray(frame.data[0].y), base_y)
        assert np.array_equal(np.asarray(frame.data[1].x), base_x)
        assert np.array_equal(np.asarray(frame.data[1].y), base_y)


def test_sieve_animation_preserves_explicit_projection_width():
    figure = build_sieve_animation(1, 30, (2, 3, 5), grid_width=7)
    x = np.asarray(figure.data[0].x)
    y = np.asarray(figure.data[0].y)

    assert int(x.min()) == 0
    assert int(x.max()) == 6
    assert int(y.min()) == 0
    assert int(y.max()) == 4

    settled = next(frame for frame in figure.frames if frame.name == "prime_5_settle")
    assert np.array_equal(np.asarray(settled.data[0].x), x)
    assert np.array_equal(np.asarray(settled.data[0].y), y)


def test_prime_cascade_visits_actual_multiples_and_only_new_resolutions_turn_amber():
    figure = build_sieve_animation(1, 30, (2, 3, 5))
    _, previous_survives, _ = filter_candidates(1, 30, (2, 3))
    _, stage_survives, _ = filter_candidates(1, 30, (2, 3, 5))
    expected_new = int(np.count_nonzero(previous_survives & ~stage_survives))

    cascade_frames = [frame for frame in figure.frames if frame.name.startswith("prime_5_cascade_")]
    visited_indices = set()
    amber_count = 0

    for frame in cascade_frames:
        focus_sizes = np.asarray(frame.data[1].marker.size, dtype=float)
        visited_indices.update(np.flatnonzero(focus_sizes > 1.0).tolist())
        amber_count += sum(color == NEWLY_RESOLVED for color in frame.data[0].marker.color)

    assert {index + 1 for index in visited_indices} == {10, 15, 20, 25, 30}
    assert amber_count == expected_new


def test_settled_checkpoint_has_no_amber_and_keeps_confirmed_teal():
    primes = (2, 3, 5)
    figure = build_sieve_animation(1, 30, primes)
    values, survives, _ = filter_candidates(1, 30, primes)
    confirmed = confirmed_prime_mask(values, survives, primes)

    settled = next(frame for frame in figure.frames if frame.name == "prime_5_settle")
    colors = list(settled.data[0].marker.color)

    assert NEWLY_RESOLVED not in colors
    assert sum(color == CONFIRMED_PRIME for color in colors) == int(np.count_nonzero(confirmed))


def test_animation_uses_scatter_traces_and_fixed_ranges_for_smooth_transitions():
    figure = build_sieve_animation(1, 120, (2, 3, 5, 7))

    assert figure.data[0].type == "scatter"
    assert figure.data[1].type == "scatter"
    assert figure.layout.xaxis.autorange is False
    assert figure.layout.yaxis.autorange is False

    play_button = figure.layout.updatemenus[0].buttons[0]
    assert play_button.args[1]["frame"]["redraw"] is False
    assert play_button.args[1]["transition"]["easing"] == "cubic-in-out"
