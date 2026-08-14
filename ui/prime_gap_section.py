import numpy as np
import streamlit as st

from prime_lab.prime_gaps import (
    prime_gap_records,
    summarize_prime_gaps,
)
from ui.prime_gaps import (
    build_gap_frequency_figure,
    build_normalized_gap_figure,
    build_prime_gap_timeline,
)


def render_prime_gap_lab(
    values: np.ndarray,
    confirmed: np.ndarray,
    frontier: int | None,
    range_start: int,
    range_end: int,
    heading: str = "Prime Gap Lab",
) -> None:
    """Render an explanatory analysis of gaps between confirmed primes."""

    with st.container(border=True):
        st.subheader(heading)

        st.caption(
            "A prime gap is the distance from one confirmed prime to the next confirmed prime. "
            "This section uses only primes that the current filter sequence has already proven."
        )

        records = prime_gap_records(
            values,
            confirmed,
        )

        summary = summarize_prime_gaps(
            records
        )

        if summary is None:
            st.write(
                "Prime Gap Lab needs at least two confirmed primes inside the selected range. "
                "Apply more prime filters or choose a range containing more confirmed primes."
            )

            if frontier is not None:
                st.caption(
                    f"The current proof frontier is n < {frontier:,}. "
                    "Unresolved survivors are never treated as primes in this analysis."
                )

            return

        if (
            frontier is not None
            and frontier > range_end
        ):
            st.success(
                "Gap coverage is complete for confirmed primes inside the visible range. "
                "Every surviving candidate shown is already proven prime."
            )

        elif frontier is not None:
            st.info(
                f"This analysis stops at the confirmed region below n = {frontier:,}. "
                "Blue unresolved survivors at or above that frontier are excluded rather than guessed to be prime."
            )

        st.caption(
            f"Only gaps whose two endpoints both lie inside the selected range {range_start:,} to {range_end:,} are counted. "
            "Prime gaps crossing either range boundary are intentionally omitted."
        )

        metric_1, metric_2, metric_3, metric_4 = st.columns(4)

        metric_1.metric(
            "Confirmed gaps analyzed",
            f"{summary.gap_count:,}",
            border=True,
        )

        metric_2.metric(
            "Average gap",
            f"{summary.mean_gap:.2f}",
            border=True,
        )

        metric_3.metric(
            "Largest gap in this range",
            (
                f"{summary.largest_gap:,}  ·  "
                f"{summary.largest_gap_lower_prime:,} → "
                f"{summary.largest_gap_upper_prime:,}"
            ),
            border=True,
        )

        metric_4.metric(
            "Twin prime pairs",
            f"{summary.twin_pair_count:,}",
            border=True,
        )

        timeline_tab, frequency_tab, normalized_tab = st.tabs(
            [
                "Gap timeline",
                "Gap frequency",
                "Normalized spacing",
            ]
        )

        with timeline_tab:
            st.write(
                "Each blue point is one gap from a confirmed prime p to the next confirmed prime. "
                "Amber diamonds mark a new largest gap encountered while moving from left to right through this selected range."
            )

            st.plotly_chart(
                build_prime_gap_timeline(
                    records
                ),
                width="stretch",
                config={
                    "displaylogo": False,
                },
                key="prime_gap_timeline",
            )

            st.caption(
                "The gray dashed curve is ln(p). The prime number theorem implies that ln(p) is an asymptotic local scale for average prime spacing near p. "
                "It is not a prediction that any individual gap must equal ln(p)."
            )

        with frequency_tab:
            st.write(
                "This view counts how often each gap size occurs among the confirmed prime pairs in the selected range. "
                "A gap of 2 corresponds to a twin prime pair."
            )

            st.plotly_chart(
                build_gap_frequency_figure(
                    records
                ),
                width="stretch",
                config={
                    "displaylogo": False,
                },
                key="prime_gap_frequency",
            )

        with normalized_tab:
            st.write(
                "Raw gap sizes become harder to compare as primes grow because typical spacing also grows. "
                "This view divides each observed gap by ln(p), where p is the lower prime in the pair."
            )

            st.plotly_chart(
                build_normalized_gap_figure(
                    records
                ),
                width="stretch",
                config={
                    "displaylogo": False,
                },
                key="prime_gap_normalized",
            )

            st.caption(
                "A ratio above 1 means the observed gap is larger than the local logarithmic spacing scale. "
                "This ratio is descriptive, not a probability or statistical significance score."
            )

            st.metric(
                "Largest gap relative to ln(p)",
                (
                    f"{summary.largest_normalized_gap:.2f} ×  ·  "
                    f"{summary.largest_normalized_lower_prime:,} → "
                    f"{summary.largest_normalized_upper_prime:,}"
                ),
                border=True,
            )
