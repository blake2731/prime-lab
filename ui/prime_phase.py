from math import cos, pi, sin

import plotly.graph_objects as go

from prime_lab.prime_phase import JointPhasePoint, PrimePhaseState


CONFIRMED_PRIME = "#008A7C"
UNRESOLVED_CANDIDATE = "#2457E6"
NEWLY_RESOLVED = "#D97706"
RESOLVED_COMPOSITE = "#E3E8EF"
INK = "#172033"
MUTED = "#667085"


def build_prime_clock_figure(states: tuple[PrimePhaseState, ...], *, columns: int = 4) -> go.Figure:
    """Draw selected prime cycles as clocks whose hands encode modular phase."""

    if columns < 1:
        raise ValueError("columns must be positive")
    if not states:
        raise ValueError("at least one phase state is required")

    rows = (len(states) + columns - 1) // columns
    spacing_x = 2.9
    spacing_y = 3.05

    figure = go.Figure()

    for index, state in enumerate(states):
        row = index // columns
        column = index % columns
        center_x = column * spacing_x
        center_y = (rows - 1 - row) * spacing_y
        emphasized = state.is_relevant_divisor
        cycle_color = NEWLY_RESOLVED if emphasized else CONFIRMED_PRIME

        circle_x = []
        circle_y = []
        for step in range(81):
            angle = 2 * pi * step / 80
            circle_x.append(center_x + cos(angle))
            circle_y.append(center_y + sin(angle))

        figure.add_trace(
            go.Scatter(
                x=circle_x,
                y=circle_y,
                mode="lines",
                line={"color": cycle_color, "width": 3 if emphasized else 2},
                hoverinfo="skip",
                showlegend=False,
            )
        )

        angle = state.angle_radians
        hand_x = center_x + 0.78 * sin(angle)
        hand_y = center_y + 0.78 * cos(angle)

        figure.add_trace(
            go.Scatter(
                x=[center_x, hand_x],
                y=[center_y, hand_y],
                mode="lines+markers",
                line={"color": cycle_color, "width": 4},
                marker={"size": [5, 10], "color": cycle_color},
                hovertemplate=(
                    f"Prime cycle: {state.prime}<br>"
                    f"Integer: {state.integer:,}<br>"
                    f"Remainder: {state.remainder}<br>"
                    f"Phase: {state.phase_fraction:.4f} turns<br>"
                    f"Angle: {state.angle_degrees:.1f}°<br>"
                    f"Previous zero: {state.previous_zero:,}<br>"
                    f"Next zero: {state.next_zero:,}<br>"
                    f"Steps to next zero: {state.steps_to_next_zero}<extra></extra>"
                ),
                showlegend=False,
            )
        )

        zero_color = NEWLY_RESOLVED if emphasized else RESOLVED_COMPOSITE
        figure.add_trace(
            go.Scatter(
                x=[center_x],
                y=[center_y + 1.0],
                mode="markers",
                marker={"size": 9 if emphasized else 7, "color": zero_color},
                hovertemplate="Phase zero · exact multiple<extra></extra>",
                showlegend=False,
            )
        )

        figure.add_annotation(
            x=center_x,
            y=center_y + 1.22,
            text="phase 0",
            showarrow=False,
            font={"size": 9, "color": MUTED},
        )

        if emphasized:
            status = f"<b>Prime {state.prime}</b><br><span style='color:{NEWLY_RESOLVED}'>PHASE ZERO · divides n</span>"
        else:
            proof_note = " · in √n proof" if state.is_relevant_test_prime else ""
            status = (
                f"<b>Prime {state.prime}</b><br>"
                f"r = {state.remainder} · next zero in {state.steps_to_next_zero}{proof_note}"
            )

        figure.add_annotation(
            x=center_x,
            y=center_y - 1.30,
            text=status,
            showarrow=False,
            align="center",
            font={"size": 11, "color": INK},
        )

    width_units = max(1, min(columns, len(states))) * spacing_x
    height_units = rows * spacing_y
    figure.update_xaxes(visible=False, range=[-1.45, width_units - spacing_x + 1.45], constrain="domain")
    figure.update_yaxes(
        visible=False,
        range=[-1.65, height_units - spacing_y + 1.55],
        scaleanchor="x",
        scaleratio=1,
    )
    figure.update_layout(
        height=max(350, 285 * rows),
        margin={"l": 10, "r": 10, "t": 20, "b": 10},
        plot_bgcolor="white",
        paper_bgcolor="white",
        hovermode="closest",
    )
    return figure


def build_joint_phase_figure(
    points: tuple[JointPhasePoint, ...],
    *,
    first_prime: int,
    second_prime: int,
    current_integer: int,
) -> go.Figure:
    """Project two prime cycles onto a normalized phase square."""

    if not points:
        raise ValueError("joint phase points are required")

    period = first_prime * second_prime
    current = points[current_integer % period]

    ordinary = [point for point in points if not point.first_zero and not point.second_zero]
    one_zero = [point for point in points if point.first_zero ^ point.second_zero]
    shared_zero = [point for point in points if point.first_zero and point.second_zero]

    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=[point.first_phase for point in ordinary],
            y=[point.second_phase for point in ordinary],
            mode="markers",
            name="Neither cycle at zero",
            marker={"size": 8, "color": UNRESOLVED_CANDIDATE, "opacity": 0.42},
            customdata=[[point.integer, point.first_remainder, point.second_remainder] for point in ordinary],
            hovertemplate=(
                "Cycle position %{customdata[0]}<br>"
                f"mod {first_prime} = %{{customdata[1]}}<br>"
                f"mod {second_prime} = %{{customdata[2]}}<extra></extra>"
            ),
        )
    )
    figure.add_trace(
        go.Scatter(
            x=[point.first_phase for point in one_zero],
            y=[point.second_phase for point in one_zero],
            mode="markers",
            name="One cycle at zero",
            marker={"size": 9, "color": NEWLY_RESOLVED, "opacity": 0.75},
            customdata=[[point.integer, point.first_remainder, point.second_remainder] for point in one_zero],
            hovertemplate=(
                "Cycle position %{customdata[0]}<br>"
                f"mod {first_prime} = %{{customdata[1]}}<br>"
                f"mod {second_prime} = %{{customdata[2]}}<extra></extra>"
            ),
        )
    )
    figure.add_trace(
        go.Scatter(
            x=[point.first_phase for point in shared_zero],
            y=[point.second_phase for point in shared_zero],
            mode="markers",
            name="Shared zero",
            marker={"size": 13, "color": CONFIRMED_PRIME, "symbol": "diamond"},
            hovertemplate="Both cycles synchronize at phase zero<extra></extra>",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=[current.first_phase],
            y=[current.second_phase],
            mode="markers",
            name=f"Current n = {current_integer}",
            marker={"size": 18, "color": INK, "symbol": "circle-open", "line": {"width": 3}},
            hovertemplate=(
                f"Current integer: {current_integer}<br>"
                f"mod {first_prime} = {current.first_remainder}<br>"
                f"mod {second_prime} = {current.second_remainder}<extra></extra>"
            ),
        )
    )

    figure.update_xaxes(
        title=f"Prime {first_prime} phase · (n mod {first_prime}) / {first_prime}",
        range=[-0.04, 1.04],
        tickformat=".2f",
    )
    figure.update_yaxes(
        title=f"Prime {second_prime} phase · (n mod {second_prime}) / {second_prime}",
        range=[-0.04, 1.04],
        tickformat=".2f",
    )
    figure.update_layout(
        height=560,
        margin={"l": 40, "r": 20, "t": 35, "b": 40},
        legend={"orientation": "h", "y": 1.08},
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    return figure


def build_phase_trace_figure(
    integers: tuple[int, ...],
    states_by_prime: dict[int, tuple[PrimePhaseState, ...]],
) -> go.Figure:
    """Show normalized sawtooth phase traces for several prime cycles."""

    figure = go.Figure()
    for prime, states in states_by_prime.items():
        figure.add_trace(
            go.Scatter(
                x=list(integers),
                y=[state.phase_fraction for state in states],
                mode="lines+markers",
                name=f"Prime {prime}",
                marker={"size": 5},
                line={"width": 2},
                customdata=[state.remainder for state in states],
                hovertemplate=(
                    "n = %{x}<br>"
                    f"prime = {prime}<br>"
                    "remainder = %{customdata}<br>"
                    "phase = %{y:.3f}<extra></extra>"
                ),
            )
        )

    figure.add_hline(y=0, line={"color": NEWLY_RESOLVED, "width": 2, "dash": "dot"})
    figure.update_xaxes(title="Integer n")
    figure.update_yaxes(title="Normalized phase", range=[-0.05, 1.03])
    figure.update_layout(
        height=460,
        margin={"l": 40, "r": 20, "t": 35, "b": 40},
        legend={"orientation": "h", "y": 1.08},
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    return figure
