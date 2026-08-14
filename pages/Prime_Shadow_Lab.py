import numpy as np
import streamlit as st

from prime_lab.certification import (
    certification_frontier,
    confirmed_prime_mask,
)
from prime_lab.filters import filter_candidates
from prime_lab.prime_shadows import (
    CONFIRMED_CODE,
    NON_CANDIDATE_CODE,
    TARGET_CODE,
    UNRESOLVED_CODE,
    build_prime_shadow,
    find_shadow_matches,
    shadow_state_counts,
)
from ui.prime_shadows import build_shadow_heatmap


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


def shadow_label(code: int) -> str:
    """Translate one shadow state into a concise readable label."""

    if code == TARGET_CODE:
        return "CENTER PRIME"

    if code == CONFIRMED_CODE:
        return "PRIME"

    if code == UNRESOLVED_CODE:
        return "UNRESOLVED"

    if code == NON_CANDIDATE_CODE:
        return "NOT A CANDIDATE"

    return f"PRIME {code}"


def shadow_explanation(code: int) -> str:
    """Explain the mathematical meaning of one shadow state."""

    if code == TARGET_CODE:
        return "The center number is a confirmed prime and survives every applied filter."

    if code == CONFIRMED_CODE:
        return "This neighboring number is also mathematically confirmed prime."

    if code == UNRESOLVED_CODE:
        return "No applied filter has eliminated this number yet, but the current filter depth is not enough to prove it prime."

    if code == NON_CANDIDATE_CODE:
        return "This number is below 2 and therefore is not a prime candidate."

    return (
        f"Prime {code} is the first applied prime filter that proves this number composite. "
        "Because filters are tested in ascending order, it is also the smallest applied prime divisor that eliminates the candidate."
    )


st.set_page_config(
    page_title="Prime Shadow Lab",
    page_icon="∴",
    layout="wide",
)


st.title("Prime Shadow Lab")
st.caption(
    "Learn how divisibility removes prime candidates around a confirmed prime, then compare those local environments experimentally."
)

st.info(
    "A prime shadow records what happens to the integers surrounding a prime. "
    "For every nearby composite, Prime Lab records the first applied prime filter that proves it composite. "
    "The center remains a confirmed prime. The resulting sequence is a local sieve fingerprint."
)

with st.expander(
    "Learn the idea first",
    expanded=True,
):
    st.write(
        "Consider the neighborhood around prime 53. Instead of marking only which values are prime, "
        "record the first prime filter that eliminates each composite candidate."
    )

    st.code(
        "Integer                  49   50   51   52   [53]   54   55   56   57   58   59\n"
        "First eliminating prime   7    2    3    2   PRIME    2    5    2    3    2   PRIME"
    )

    st.write(
        "This means 49 is first resolved as composite by 7, 50 by 2, 51 by 3, and 52 by 2. "
        "The number 53 remains prime, and 59 is another confirmed prime in the same neighborhood."
    )

    st.write(
        "The purpose of the shadow is therefore not decorative. It lets us study a prime together with the divisibility structure around it. "
        "We can then ask whether distant primes have similar local environments, and whether those environments relate to prime gaps, twin primes, or other recurring structures."
    )

    st.caption(
        "Learning goal: read a shadow as a record of which prime divisors first remove neighboring integers from prime candidacy."
    )


with st.container(border=True):
    st.subheader("1. Configure the experiment")
    st.caption(
        "Choose a number range, a filter depth, and how far to inspect on each side of the center prime. "
        "Similarity comparisons use only windows that are completely inside the mathematically proven region."
    )

    col_start, col_end, col_filter, col_radius = st.columns(
        [1, 1, 1.3, 1]
    )

    with col_start:
        range_start = st.number_input(
            "Range start",
            min_value=1,
            value=1,
            step=1,
            help="The first integer included in the experiment.",
        )

    with col_end:
        range_end = st.number_input(
            "Range end",
            min_value=2,
            value=5000,
            step=1,
            help="The last integer included in the experiment.",
        )

    with col_filter:
        active_prime = st.selectbox(
            "Apply prime filters through",
            FILTER_PRIMES,
            index=len(FILTER_PRIMES) - 1,
            format_func=lambda value: f"Prime {value}",
            help=(
                "Choosing Prime 23 applies every prime filter from 2 through 23 in sequence. "
                "A deeper filter sequence confirms a larger part of the range."
            ),
        )

    with col_radius:
        radius = int(
            st.number_input(
                "Shadow radius",
                min_value=5,
                max_value=60,
                value=24,
                step=1,
                help=(
                    "Radius 24 examines 24 integers before and 24 integers after the center prime."
                ),
            )
        )


if range_end < range_start:
    st.error("Range end must be greater than or equal to range start.")
    st.stop()

range_size = range_end - range_start + 1

if range_size > 5000:
    st.warning(
        "Prime Shadow Lab is currently limited to 5,000 visible integers so it stays aligned with the rest of Prime Lab."
    )
    st.stop()

if range_size < (2 * radius + 1):
    st.warning(
        "The selected range is too small for this shadow radius. Reduce the radius or widen the range."
    )
    st.stop()

active_index = FILTER_PRIMES.index(active_prime)
applied_primes = FILTER_PRIMES[: active_index + 1]

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

frontier = certification_frontier(applied_primes)

confirmed_values = values[confirmed].astype(
    np.int64,
    copy=False,
)

proven_window_end = min(
    range_end,
    frontier - 1,
)

eligible_mask = (
    (confirmed_values - radius >= range_start)
    & (confirmed_values + radius <= proven_window_end)
)

eligible_targets = confirmed_values[eligible_mask]

if len(eligible_targets) == 0:
    st.warning(
        "There are no confirmed primes with a complete proven shadow window at this filter stage. "
        "Apply more filters, reduce the radius, or widen the range."
    )
    st.stop()

midpoint = (range_start + proven_window_end) / 2
initial_target_index = int(
    np.argmin(
        np.abs(eligible_targets - midpoint)
    )
)

control_left, control_right = st.columns([1, 2])

with control_left:
    target_prime = int(
        st.selectbox(
            "Center prime",
            [int(value) for value in eligible_targets],
            index=initial_target_index,
            help=(
                "Only confirmed primes whose entire shadow window is already proven are available for comparison."
            ),
        )
    )

with control_right:
    st.metric(
        "Proven region available for complete shadows",
        f"{range_start:,} to {proven_window_end:,}",
        border=True,
        help=(
            f"The current proof frontier is n < {frontier:,}. Complete shadow windows are kept below that boundary."
        ),
    )


target_shadow = build_prime_shadow(
    target_prime,
    radius,
    applied_primes,
)

target_counts = shadow_state_counts(target_shadow)

confirmed_list = [int(value) for value in confirmed_values]
target_confirmed_index = confirmed_list.index(target_prime)

previous_prime = (
    confirmed_list[target_confirmed_index - 1]
    if target_confirmed_index > 0
    else None
)

next_prime = (
    confirmed_list[target_confirmed_index + 1]
    if target_confirmed_index + 1 < len(confirmed_list)
    else None
)

left_gap = (
    target_prime - previous_prime
    if previous_prime is not None
    else None
)

right_gap = (
    next_prime - target_prime
    if next_prime is not None
    else None
)


with st.container(border=True):
    st.subheader("2. Read one prime shadow")

    st.write(
        f"The shadow below is centered on confirmed prime **{target_prime:,}** and examines offsets from **-{radius}** through **+{radius}**. "
        "At every composite position, the shadow records the first prime filter that proves that neighboring integer composite."
    )

    metric_1, metric_2, metric_3, metric_4, metric_5 = st.columns(5)

    metric_1.metric(
        "Numbers in the shadow",
        f"{2 * radius + 1:,}",
        border=True,
    )

    metric_2.metric(
        "Composite neighbors resolved",
        f"{target_counts['filtered_composites']:,}",
        border=True,
    )

    metric_3.metric(
        "Confirmed prime neighbors",
        f"{target_counts['confirmed_neighbors']:,}",
        border=True,
    )

    metric_4.metric(
        "Gap to previous prime",
        f"{left_gap:,}" if left_gap is not None else "Boundary",
        border=True,
    )

    metric_5.metric(
        "Gap to next prime",
        f"{right_gap:,}" if right_gap is not None else "Boundary",
        border=True,
    )

    center_index = target_shadow.offsets.index(0)
    example_start = max(0, center_index - 4)
    example_end = min(
        len(target_shadow.offsets),
        center_index + 7,
    )

    example_rows = []

    for offset, value, code in zip(
        target_shadow.offsets[example_start:example_end],
        target_shadow.values[example_start:example_end],
        target_shadow.state_codes[example_start:example_end],
        strict=True,
    ):
        example_rows.append(
            {
                "Offset": f"{offset:+d}",
                "Integer": value,
                "State": shadow_label(code),
                "Interpretation": shadow_explanation(code),
            }
        )

    st.markdown("**Example: interpret a small section before reading the full visualization**")

    st.dataframe(
        example_rows,
        width="stretch",
        hide_index=True,
    )

    st.caption(
        "If the State column says PRIME 7, the neighboring integer is composite and 7 is the first applied prime filter that proves it. "
        "PRIME means the neighboring integer is itself confirmed prime."
    )

    st.plotly_chart(
        build_shadow_heatmap(
            (target_shadow,),
            title=f"Prime {target_prime:,} local sieve fingerprint",
        ),
        width="stretch",
        config={"displaylogo": False},
        key="prime_shadow_target",
    )

    higher_shadow_share = (
        target_counts["higher_prime_shadows"]
        / max(target_counts["filtered_composites"], 1)
    )

    st.write(
        f"Within this window, **{target_counts['higher_prime_shadows']:,}** composite neighbors are not resolved by 2, 3, or 5 and require a larger prime filter. "
        f"That is **{higher_shadow_share:.1%}** of the resolved composite neighbors. These positions are useful when looking beyond the strongest repeating effects of small primes."
    )


with st.container(border=True):
    st.subheader("3. Compare local environments")

    st.write(
        "Prime Shadow Lab can now ask whether distant primes have similar divisibility environments at the same relative offsets. "
        "The initial comparison method measures exact state agreement position by position."
    )

    st.caption(
        "Important: repeating divisibility by 2, 3, and 5 can dominate a raw comparison. "
        "The exploratory deeper score therefore ignores positions where either shadow is first resolved by 2, 3, or 5. "
        "Agreement must always be interpreted together with the number of positions that remain available for comparison."
    )

    matches = find_shadow_matches(
        target_prime,
        [int(value) for value in eligible_targets],
        radius,
        applied_primes,
        deep_ignore=(2, 3, 5),
    )

    if not matches:
        st.write(
            "There are not enough other confirmed primes with complete windows to perform a similarity search."
        )

    else:
        match_count = int(
            st.select_slider(
                "Number of closest shadows to inspect",
                options=[5, 8, 10, 12, 15],
                value=8,
            )
        )

        top_matches = matches[:match_count]
        strongest_match = top_matches[0]

        same_mod_30 = sum(
            match.residue_mod_30 == target_prime % 30
            for match in top_matches
        )

        total_noncenter_positions = 2 * radius
        deep_coverage = (
            strongest_match.deep_positions_compared
            / total_noncenter_positions
        )

        similarity_metric_1, similarity_metric_2, similarity_metric_3, similarity_metric_4 = st.columns(4)

        similarity_metric_1.metric(
            "Closest exploratory match",
            f"Prime {strongest_match.prime:,}",
            border=True,
        )

        similarity_metric_2.metric(
            "Agreement on compared positions",
            f"{strongest_match.deep_similarity:.1%}",
            border=True,
        )

        similarity_metric_3.metric(
            "Positions compared",
            f"{strongest_match.deep_positions_compared} of {total_noncenter_positions}",
            border=True,
        )

        similarity_metric_4.metric(
            "Comparison coverage",
            f"{deep_coverage:.1%}",
            border=True,
            help=(
                "Coverage is the fraction of noncenter positions still available after positions dominated by 2, 3, and 5 are removed."
            ),
        )

        if deep_coverage < 0.25:
            st.warning(
                "This similarity result is based on relatively few positions after controlling for 2, 3, and 5. "
                "Treat the percentage as preliminary rather than as strong evidence of a meaningful relationship."
            )
        else:
            st.info(
                f"Among the top {match_count} exploratory matches, {same_mod_30} share the same modulo 30 residue class as the center prime. "
                "This helps indicate whether familiar wheel structure may still be contributing to the result."
            )

        comparison_shadows = [target_shadow]
        comparison_shadows.extend(
            build_prime_shadow(
                match.prime,
                radius,
                applied_primes,
            )
            for match in top_matches
        )

        st.plotly_chart(
            build_shadow_heatmap(
                tuple(comparison_shadows),
                title=(
                    f"Prime {target_prime:,} and its closest exploratory shadow matches"
                ),
            ),
            width="stretch",
            config={"displaylogo": False},
            key="prime_shadow_matches",
        )

        match_rows = [
            {
                "Prime": match.prime,
                "Distance from center": match.distance,
                "Prime mod 30": match.residue_mod_30,
                "Full shadow agreement": f"{match.full_similarity:.1%}",
                "Agreement after controlling for 2, 3, 5": f"{match.deep_similarity:.1%}",
                "Positions compared": match.deep_positions_compared,
                "Coverage": (
                    f"{match.deep_positions_compared / total_noncenter_positions:.1%}"
                ),
            }
            for match in top_matches
        ]

        with st.expander(
            "Inspect the evidence behind the similarity scores",
            expanded=False,
        ):
            st.dataframe(
                match_rows,
                width="stretch",
                hide_index=True,
            )

        st.caption(
            "Similarity is an exploratory observation, not evidence of a new law by itself. "
            "A useful pattern should persist across larger independent ranges, different shadow radii, and stronger controls for known modular structure."
        )


with st.container(border=True):
    st.subheader("4. Continue the investigation")

    st.write(
        "Prime Shadow Lab is designed as both a learning tool and an experimental instrument. "
        "First, it makes the sieve process visible: nearby composites are classified by the earliest prime filter that resolves them. "
        "Second, it lets us formulate and test questions about whether local divisibility environments recur around different primes."
    )

    st.markdown(
        """
**Questions worth testing**

1. Do distant primes retain unusual local similarity after obvious small prime structure is controlled for?
2. Do particular shadow patterns occur more often around twin primes or unusually large prime gaps?
3. Does an apparent pattern survive changes in shadow radius and filter depth?
4. Does the same effect reproduce in a different number range?
        """
    )

    st.caption(
        "The goal is to make each experiment understandable enough to learn from, while keeping the underlying mathematics explicit enough to test critically."
    )
