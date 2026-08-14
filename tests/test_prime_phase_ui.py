from prime_lab.prime_phase import joint_phase_cycle, phase_state, phase_states
from ui.prime_phase import (
    CONFIRMED_PRIME,
    NEWLY_RESOLVED,
    build_joint_phase_figure,
    build_phase_trace_figure,
    build_prime_clock_figure,
)


def test_clock_figure_contains_one_circle_and_hand_per_prime():
    states = phase_states(30, (2, 3, 5, 7))
    figure = build_prime_clock_figure(states)

    assert len(figure.data) == 12
    assert any(trace.line.color == CONFIRMED_PRIME for trace in figure.data if hasattr(trace, "line"))
    assert any(
        trace.line.color == NEWLY_RESOLVED
        for trace in figure.data
        if hasattr(trace, "line") and trace.line.color is not None
    )


def test_joint_phase_figure_marks_current_state_and_shared_zero():
    points = joint_phase_cycle(3, 5)
    figure = build_joint_phase_figure(
        points,
        first_prime=3,
        second_prime=5,
        current_integer=30,
    )

    names = [trace.name for trace in figure.data]
    assert "Shared zero" in names
    assert "Current n = 30" in names


def test_phase_trace_figure_uses_normalized_phase_values():
    integers = tuple(range(8, 13))
    states_by_prime = {
        2: tuple(phase_state(integer, 2) for integer in integers),
        3: tuple(phase_state(integer, 3) for integer in integers),
    }
    figure = build_phase_trace_figure(integers, states_by_prime)

    assert len(figure.data) == 2
    assert list(figure.data[0].x) == list(integers)
    assert all(0 <= value < 1 for value in figure.data[0].y)
