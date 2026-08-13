import numpy as np
import streamlit as st

from prime_lab.filters import filter_candidates
from ui.candidate_grid import build_candidate_figure
from ui.sieve_animation import build_sieve_animation

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


st.title("Prime Lab")

st.caption("Computational Number Theory Laboratory  •  Candidate Filter Visualizer")


with st.container(border=True):
    st.subheader("Experiment controls")

    col_start, col_end, col_filter = st.columns([1, 1, 1.25])

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

    if applied_primes:
        figure = build_sieve_animation(
            range_start,
            range_end,
            applied_primes,
        )

    else:
        figure = build_candidate_figure(
            values,
            survives,
            eliminated_by,
            active_prime,
        )

    st.plotly_chart(
        figure,
        width="stretch",
        config={
            "displaylogo": False,
        },
        key="candidate_landscape",
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
