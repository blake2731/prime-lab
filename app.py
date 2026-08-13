import time

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from prime_lab.filters import filter_candidates

FILTER_PRIMES = (
    2,
    3,
    5,
    7,
    11,
    13,
    17,
    19,
    23,
    29,
    31,
)


st.set_page_config(
    page_title="Prime Lab",
    page_icon="∴",
    layout="wide",
)


def build_candidate_figure(
    values: np.ndarray,
    survives: np.ndarray,
    eliminated_by: np.ndarray,
    active_prime: int | None,
) -> go.Figure:
    """Create a precise tiled candidate field."""

    count = len(values)

    grid_width = max(
        10,
        int(np.ceil(np.sqrt(count))),
    )

    grid_height = int(np.ceil(count / grid_width))

    total_cells = grid_width * grid_height

    status = np.full(
        total_cells,
        np.nan,
        dtype=float,
    )

    hover_text = np.full(
        total_cells,
        "",
        dtype=object,
    )

    status[:count] = 0

    survivor_indices = np.flatnonzero(survives)

    status[survivor_indices] = 1

    if active_prime is not None:
        current_mask = eliminated_by == active_prime

        current_indices = np.flatnonzero(current_mask)

        status[current_indices] = 2

    for index, value in enumerate(values):
        if survives[index]:
            state = "Surviving candidate"

        elif active_prime is not None and eliminated_by[index] == active_prime:
            state = f"Removed by prime {active_prime}"

        elif eliminated_by[index] > 0:
            state = "Previously eliminated " f"by prime {eliminated_by[index]}"

        else:
            state = "Not a prime candidate"

        hover_text[index] = f"<b>{int(value):,}</b>" f"<br>{state}"

    status_grid = status.reshape(
        grid_height,
        grid_width,
    )

    hover_grid = hover_text.reshape(
        grid_height,
        grid_width,
    )

    figure = go.Figure()

    figure.add_trace(
        go.Heatmap(
            z=status_grid,
            text=hover_grid,
            zmin=0,
            zmax=2,
            colorscale=[
                [0.000000, "#E3E8EF"],
                [0.333333, "#E3E8EF"],
                [0.333334, "#2457E6"],
                [0.666666, "#2457E6"],
                [0.666667, "#D97706"],
                [1.000000, "#D97706"],
            ],
            showscale=False,
            xgap=1,
            ygap=1,
            hoverongaps=False,
            hovertemplate=("%{text}" "<extra></extra>"),
        )
    )

    legend_entries = (
        (
            "Surviving candidate",
            "#2457E6",
        ),
        (
            "Previously eliminated",
            "#E3E8EF",
        ),
        (
            "Removed by current filter",
            "#D97706",
        ),
    )

    for name, color in legend_entries:
        figure.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode="markers",
                marker={
                    "size": 11,
                    "color": color,
                    "symbol": "square",
                },
                name=name,
                hoverinfo="skip",
            )
        )

    figure.update_layout(
        height=650,
        margin={
            "l": 10,
            "r": 10,
            "t": 45,
            "b": 10,
        },
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "left",
            "x": 0,
            "itemclick": False,
            "itemdoubleclick": False,
        },
    )

    figure.update_xaxes(
        visible=False,
        fixedrange=True,
    )

    figure.update_yaxes(
        visible=False,
        fixedrange=True,
        autorange="reversed",
        scaleanchor="x",
        scaleratio=1,
    )

    return figure


st.title("Prime Lab")

st.caption("Computational Number Theory Laboratory  •  Candidate Filter Visualizer")


with st.container(border=True):
    st.subheader("Experiment controls")

    col_start, col_end, col_filter, col_play = st.columns([1, 1, 1.25, 0.8])

    with col_start:
        range_start = st.number_input(
            "Range start",
            min_value=1,
            value=1,
            step=1,
        )

    with col_end:
        range_end = st.number_input(
            "Range end",
            min_value=2,
            value=500,
            step=1,
        )

    with col_filter:
        filter_options = [
            None,
            *FILTER_PRIMES,
        ]

        active_prime = st.selectbox(
            "Apply filters through",
            filter_options,
            index=0,
            format_func=lambda value: (
                "No filters" if value is None else f"Prime {value}"
            ),
        )

    with col_play:
        st.write("")

        play_animation = st.button(
            "Run sequence",
            type="primary",
            icon=":material/play_arrow:",
            width="stretch",
            disabled=active_prime is None,
        )


if range_end < range_start:
    st.error("Range end must be greater than or equal to range start.")
    st.stop()


range_size = range_end - range_start + 1


if range_size > 5000:
    st.warning("The first visual build is limited to 5,000 visible integers.")
    st.stop()


if active_prime is None:
    applied_primes = ()

else:
    active_index = FILTER_PRIMES.index(active_prime)

    applied_primes = FILTER_PRIMES[: active_index + 1]


values, survives, eliminated_by = filter_candidates(
    range_start,
    range_end,
    applied_primes,
)


initial_candidates = int(np.count_nonzero(values >= 2))

survivor_count = int(np.count_nonzero(survives))

eliminated_count = initial_candidates - survivor_count


if active_prime is None:
    newly_eliminated = 0

else:
    newly_eliminated = int(np.count_nonzero(eliminated_by == active_prime))


survival_rate = survivor_count / initial_candidates if initial_candidates else 0


metric_1, metric_2, metric_3, metric_4 = st.columns(4)

metric_1.metric(
    "Integers",
    f"{range_size:,}",
    border=True,
)

metric_2.metric(
    "Candidates remaining",
    f"{survivor_count:,}",
    border=True,
)

metric_3.metric(
    "Eliminated",
    f"{eliminated_count:,}",
    border=True,
)

metric_4.metric(
    "Candidate survival",
    f"{survival_rate:.2%}",
    border=True,
)


with st.container(border=True):
    st.subheader("Candidate landscape")

    animation_status = st.empty()

    chart_placeholder = st.empty()

    if play_animation and applied_primes:
        (
            initial_values,
            initial_survives,
            initial_eliminated_by,
        ) = filter_candidates(
            range_start,
            range_end,
            (),
        )

        animation_status.caption("Starting candidate population")

        chart_placeholder.plotly_chart(
            build_candidate_figure(
                initial_values,
                initial_survives,
                initial_eliminated_by,
                None,
            ),
            width="stretch",
            config={
                "displaylogo": False,
            },
            key="animation_start",
        )

        time.sleep(0.6)

        for step, prime in enumerate(applied_primes):
            stage_primes = applied_primes[: step + 1]

            (
                stage_values,
                stage_survives,
                stage_eliminated_by,
            ) = filter_candidates(
                range_start,
                range_end,
                stage_primes,
            )

            removed_now = int(np.count_nonzero(stage_eliminated_by == prime))

            remaining_now = int(np.count_nonzero(stage_survives))

            animation_status.markdown(
                f"**Filter {prime}**  "
                f"Removed `{removed_now:,}` candidates  "
                f"Remaining `{remaining_now:,}`"
            )

            chart_placeholder.plotly_chart(
                build_candidate_figure(
                    stage_values,
                    stage_survives,
                    stage_eliminated_by,
                    prime,
                ),
                width="stretch",
                config={
                    "displaylogo": False,
                },
                key=f"animation_hit_{prime}",
            )

            time.sleep(0.75)

            if prime != applied_primes[-1]:
                chart_placeholder.plotly_chart(
                    build_candidate_figure(
                        stage_values,
                        stage_survives,
                        stage_eliminated_by,
                        None,
                    ),
                    width="stretch",
                    config={
                        "displaylogo": False,
                    },
                    key=f"animation_settle_{prime}",
                )

                time.sleep(0.22)

    else:
        animation_status.empty()

        chart_placeholder.plotly_chart(
            build_candidate_figure(
                values,
                survives,
                eliminated_by,
                active_prime,
            ),
            width="stretch",
            config={
                "displaylogo": False,
            },
            key="candidate_landscape_static",
        )


with st.container(border=True):
    st.subheader("Current filter")

    if active_prime is None:
        st.write(
            "No divisibility filters have been applied. "
            "Every integer greater than 1 begins as a candidate."
        )

    else:
        detail_left, detail_right = st.columns([2, 1])

        with detail_left:
            st.write(
                f"Every prime filter through {active_prime} " f"has now been applied."
            )

            st.code(f"n % {active_prime} == 0")

            st.caption(
                "Numbers removed by earlier filters appear in gray. "
                "Numbers removed by the current filter appear in amber."
            )

        with detail_right:
            st.metric(
                f"Removed by {active_prime}",
                f"{newly_eliminated:,}",
                border=True,
            )

    st.caption(
        "Survival does not prove primality. "
        "It only means the number has survived every filter applied so far."
    )
