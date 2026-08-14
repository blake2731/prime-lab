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
            "Every measurement below uses proven prime endpoints only."
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
            coverage_text = (
                "Complete coverage: every surviving candidate in the visible range is already proven prime."
            )
            st.success(coverage_text)

        elif frontier is not None:
            coverage_text = (
                f"Partial coverage: gap analysis uses only the confirmed region below n = {frontier:,}."
            )
            st.info(
                coverage_text
                + " Unresolved survivors at or above the frontier are excluded rather than guessed to be prime."
            )

        st.caption(
            f"Only gaps whose two endpoints both lie inside {range_start:,} to {range_end:,} are counted. "
            "A gap crossing either boundary is omitted."
        )

        metric_1, metric_2, metric_3, metric_4 = st.columns(4)

        metric_1.metric(
            "Gaps analyzed",
            f"{summary.gap_count:,}",
            border=True,
        )

        metric_2.metric(
            "Typical gap",
            f"Median {summary.median_gap:.0f}",
            border=True,
            help=(
                f"The average gap is {summary.mean_gap:.2f}. Median is shown because a few large gaps can pull the average upward."
            ),
        )

        metric_3.metric(
            "Largest observed gap",
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

        twin_share = (
            summary.twin_pair_count
            / summary.gap_count
        )

        st.markdown("**What stands out in this experiment**")
        insight_left, insight_middle, insight_right = st.columns(3)

        with insight_left:
            st.write(
                f"The most common observed gap is **{summary.most_common_gap}**, appearing **{summary.most_common_gap_count:,} times**."
            )

        with insight_middle:
            st.write(
                f"Twin prime gaps of 2 make up **{twin_share:.1%}** of the confirmed gaps in this selected range."
            )

        with insight_right:
            st.write(
                f"The largest spacing is **{summary.largest_normalized_gap:.2f} × ln(p)** relative to its local logarithmic spacing scale."
            )

        timeline_tab, frequency_tab, normalized_tab = st.tabs(
            [
                "Spacing across the range",
                "Which gaps occur most",
                "Compare gaps across scale",
            ]
        )

        with timeline_tab:
            st.write(
                "Each blue point is one observed gap. The dark line is a 25 gap rolling average when enough data are available. "
                "Amber diamonds mark new record gaps encountered while moving through this selected range."
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
                "The gray dashed curve is ln(p), an asymptotic local scale for average prime spacing near p. "
                "Individual prime gaps can lie well above or below it."
            )

        with frequency_tab:
            st.write(
                "This view counts how often each gap size occurs among the confirmed prime pairs in the selected range. "
                "A gap of 2 is a twin prime pair."
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
                "Prime spacing tends to grow as numbers grow. To make gaps at different magnitudes easier to compare, "
                "this view divides each observed gap by ln(p), using the lower prime p in the pair."
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
                "A value of 1 means the gap equals the local logarithmic spacing scale. "
                "A value of 2 means it is twice that scale. This is descriptive, not a probability or significance score."
            )
