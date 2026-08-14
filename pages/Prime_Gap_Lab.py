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
    "How far apart are consecutive primes, and how does that spacing change as the numbers grow?"
)

with st.expander(
    "What this lab measures",
    expanded=False,
):
    st.write(
        "Prime Gap Lab measures the distance between consecutive confirmed primes. "
        "It never promotes an unresolved survivor to prime status just to fill a graph."
    )
    st.write(
        "The main views answer three different questions: how spacing changes across the range, "
        "which gap sizes occur most often, and how unusually large a gap is relative to the local scale ln(p)."
    )


with st.container(border=True):
    st.subheader("Experiment")
    st.caption(
        "Choose the visible range, then choose how far the sieve should prove primality."
    )

    col_start, col_end, col_filter = st.columns(
        [
            1,
            1,
            1.35,
        ]
    )

    with col_start:
        range_start = st.number_input(
            "Range start",
            min_value=1,
            value=1,
            step=1,
            help="The first integer included in the gap experiment.",
        )

    with col_end:
        range_end = st.number_input(
            "Range end",
            min_value=2,
            value=5000,
            step=1,
            help="The last integer included in the gap experiment.",
        )

    with col_filter:
        active_prime = st.selectbox(
            "Prove using prime filters through",
            FILTER_PRIMES,
            index=len(FILTER_PRIMES) - 1,
            format_func=lambda value: f"Prime {value}",
            help=(
                "Choosing Prime 23 applies every prime filter from 2 through 23 in sequence. "
                "The next prime determines the proof frontier."
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

coverage_end = min(
    int(range_end),
    int(frontier - 1),
)

metric_1, metric_2, metric_3, metric_4 = st.columns(4)

metric_1.metric(
    "Confirmed primes",
    f"{confirmed_count:,}",
    border=True,
)

metric_2.metric(
    "Unresolved excluded",
    f"{unresolved_count:,}",
    border=True,
)

metric_3.metric(
    "Proof frontier",
    f"n < {frontier:,}",
    border=True,
)

metric_4.metric(
    "Confirmed coverage through",
    f"{coverage_end:,}",
    border=True,
)

st.caption(
    "The proof frontier is a guarantee boundary. Values at or above it may still be prime, but Prime Gap Lab excludes them until the applied filters are sufficient to prove them."
)


render_prime_gap_lab(
    values,
    confirmed,
    frontier,
    int(range_start),
    int(range_end),
)
