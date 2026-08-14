import numpy as np
import streamlit as st

from prime_lab.certification import (
    certification_frontier,
    confirmed_prime_mask,
)
from prime_lab.filters import filter_candidates
from ui.prime_gap_section import render_prime_gap_lab


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
    37,
    41,
    43,
    47,
    53,
    59,
    61,
    67,
)


st.set_page_config(
    page_title="Prime Gap Lab",
    page_icon="∴",
    layout="wide",
)


st.title("Prime Gap Lab")
st.caption(
    "Measure how spacing between confirmed primes changes across a selected number range."
)

st.info(
    "Prime Gap Lab never assumes that an unresolved survivor is prime. "
    "Only numbers already proven prime by the selected filter sequence are used to create gaps."
)


with st.container(border=True):
    st.subheader("Choose the gap experiment")
    st.caption(
        "Choose a visible range and how far the prime filtering process should run. "
        "A higher filter stage pushes the proof frontier farther into the range."
    )

    col_start, col_end, col_filter = st.columns(
        [
            1,
            1,
            1.3,
        ]
    )

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
            value=5000,
            step=1,
        )

    with col_filter:
        active_prime = st.selectbox(
            "Apply prime filters through",
            FILTER_PRIMES,
            index=len(FILTER_PRIMES) - 1,
            format_func=lambda value: f"Prime {value}",
            help=(
                "Choosing Prime 23 applies every prime filter from 2 through 23 in sequence."
            ),
        )


if range_end < range_start:
    st.error(
        "Range end must be greater than or equal to range start."
    )
    st.stop()


range_size = (
    range_end
    - range_start
    + 1
)


if range_size > 5000:
    st.warning(
        "Prime Gap Lab is currently limited to 5,000 visible integers so it stays aligned with the main Prime Lab experiment size."
    )
    st.stop()


active_index = FILTER_PRIMES.index(
    active_prime
)

applied_primes = FILTER_PRIMES[
    : active_index + 1
]

values, survives, _ = filter_candidates(
    range_start,
    range_end,
    applied_primes,
)

confirmed = confirmed_prime_mask(
    values,
    survives,
    applied_primes,
)

frontier = certification_frontier(
    applied_primes
)

confirmed_count = int(
    np.count_nonzero(
        confirmed
    )
)

unresolved_count = int(
    np.count_nonzero(
        survives
        & ~confirmed
    )
)

metric_1, metric_2, metric_3 = st.columns(3)

metric_1.metric(
    "Confirmed primes in range",
    f"{confirmed_count:,}",
    border=True,
)

metric_2.metric(
    "Unresolved survivors excluded",
    f"{unresolved_count:,}",
    border=True,
)

metric_3.metric(
    "Proof frontier",
    (
        f"n < {frontier:,}"
        if frontier is not None
        else "None yet"
    ),
    border=True,
)


render_prime_gap_lab(
    values,
    confirmed,
    frontier,
    int(range_start),
    int(range_end),
)
