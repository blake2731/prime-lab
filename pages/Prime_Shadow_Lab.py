import numpy as np
import streamlit as st

from prime_lab.certification import (
    certification_frontier,
    confirmed_prime_mask,
)
from prime_lab.filters import filter_candidates
from prime_lab.prime_shadows import (
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


st.set_page_config(
    page_title="Prime Shadow Lab",
    page_icon="∴",
    layout="wide",
)


st.title("Prime Shadow Lab")
st.caption(
    "Study a prime by the divisibility structure of the integers surrounding it."
)

st.info(
    "Prime Shadow Lab does not ask only where a prime sits on the number line. "
    "It asks which small prime first eliminates each neighboring integer, creating a local sieve fingerprint around the center prime."
)

with st.expander(
    "What is a prime shadow?",
    expanded=False,
):
    st.write(
        "Take a confirmed prime and look the same distance to its left and right. "
        "Every nearby composite is assigned to the first applied prime filter that proves it composite. "
        "Because filters are applied in ascending prime order, that label is the smallest applied prime divisor responsible for eliminating the number."
    )

    st.write(
        "Confirmed prime neighbors stay visible as primes. Unresolved survivors remain separate so Prime Lab never quietly treats an unproven candidate as prime."
    )

    st.write(
        "The result is a position by position fingerprint of the local sieve environment. "
        "Two distant primes can then be compared by asking how often the same relative positions have the same mathematical state."
    )


with st.container(border=True):
    st.subheader("1. Choose the experiment")
    st.caption(
        "The target prime must have a complete shadow window inside the selected range so comparisons do not contain boundary artifacts."
    )

    col_start, col_end, col_filter, col_radius = st.columns(
        [
            1,
            1,
            1.3,
            1,
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
                "A higher filter stage confirms a larger portion of the range and identifies more composite neighbors by their smallest tested prime divisor."
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
                    "Radius 24 shows 24 integers on each side of the center prime, plus the center itself."
                ),
            )
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
        "Prime Shadow Lab is currently limited to 5,000 visible integers so it stays aligned with the rest of Prime Lab."
    )
    st.stop()


if range_size < (2 * radius + 1):
    st.warning(
        "The selected range is too small for this shadow radius. Reduce the radius or widen the range."
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

confirmed_values = values[
    confirmed
].astype(
    np.int64,
    copy=False,
)

eligible_mask = (
    (confirmed_values - radius >= range_start)
    & (confirmed_values + radius <= range_end)
)

eligible_targets = confirmed_values[
    eligible_mask
]


if len(eligible_targets) == 0:
    st.warning(
        "There are no confirmed primes with a complete shadow window at this filter stage. Apply more filters, reduce the radius, or widen the range."
    )
    st.stop()


midpoint = (
    range_start
    + range_end
) / 2

initial_target_index = int(
    np.argmin(
        np.abs(
            eligible_targets
            - midpoint
        )
    )
)

control_left, control_right = st.columns(
    [
        1,
        2,
    ]
)

with control_left:
    target_prime = int(
        st.selectbox(
            "Center prime",
            [
                int(value)
                for value in eligible_targets
            ],
            index=initial_target_index,
            help=(
                "Only confirmed primes with a complete window on both sides are offered here."
            ),
        )
    )

with control_right:
    st.metric(
        "Current proof frontier",
        f"n < {frontier:,}",
        border=True,
        help=(
            "Surviving candidates below this frontier are mathematically confirmed prime."
        ),
    )


target_shadow = build_prime_shadow(
    target_prime,
    radius,
    applied_primes,
)

target_counts = shadow_state_counts(
    target_shadow
)

confirmed_list = [
    int(value)
    for value in confirmed_values
]

target_confirmed_index = confirmed_list.index(
    target_prime
)

previous_prime = (
    confirmed_list[
        target_confirmed_index - 1
    ]
    if target_confirmed_index > 0
    else None
)

next_prime = (
    confirmed_list[
        target_confirmed_index + 1
    ]
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
    st.subheader("2. Read this prime's local sieve fingerprint")

    st.write(
        f"The fingerprint below is centered on confirmed prime **{target_prime:,}** and covers offsets from **-{radius}** through **+{radius}**. "
        "The same offset always means the same relative position when two primes are compared."
    )

    metric_1, metric_2, metric_3, metric_4, metric_5 = st.columns(5)

    metric_1.metric(
        "Window width",
        f"{2 * radius + 1:,}",
        border=True,
    )

    metric_2.metric(
        "Composite neighbors resolved",
        f"{target_counts['filtered_composites']:,}",
        border=True,
    )

    metric_3.metric(
        "Prime neighbors confirmed",
        f"{target_counts['confirmed_neighbors']:,}",
        border=True,
    )

    metric_4.metric(
        "Gap before",
        (
            f"{left_gap:,}"
            if left_gap is not None
            else "Boundary"
        ),
        border=True,
    )

    metric_5.metric(
        "Gap after",
        (
            f"{right_gap:,}"
            if right_gap is not None
            else "Boundary"
        ),
        border=True,
    )

    st.plotly_chart(
        build_shadow_heatmap(
            (target_shadow,),
            title=(
                f"Prime {target_prime:,} local shadow"
            ),
        ),
        width="stretch",
        config={
            "displaylogo": False,
        },
        key="prime_shadow_target",
    )

    st.caption(
        "The center line is the target prime. For composite cells, the color identifies the smallest applied prime divisor that eliminated that integer. "
        "Confirmed prime neighbors and unresolved survivors are shown as different states rather than being merged."
    )

    higher_shadow_share = (
        target_counts["higher_prime_shadows"]
        / max(
            target_counts["filtered_composites"],
            1,
        )
    )

    st.write(
        f"In this window, **{target_counts['higher_prime_shadows']:,}** resolved composite positions are first explained by primes larger than 5. "
        f"That is **{higher_shadow_share:.1%}** of the resolved composite neighbors, after the strongest 2, 3, and 5 wheel effects are accounted for separately."
    )


with st.container(border=True):
    st.subheader("3. Search for distant primes with similar shadows")

    st.write(
        "A raw comparison can be dominated by the repeating divisibility patterns of 2, 3, and 5. "
        "Prime Shadow Lab therefore also computes a deeper comparison that ignores any position where either shadow is first eliminated by 2, 3, or 5."
    )

    st.caption(
        "The deeper score asks a narrower question: after removing the obvious base wheel structure, how often do the remaining relative positions still have exactly the same mathematical state?"
    )

    matches = find_shadow_matches(
        target_prime,
        [
            int(value)
            for value in eligible_targets
        ],
        radius,
        applied_primes,
        deep_ignore=(
            2,
            3,
            5,
        ),
    )

    if not matches:
        st.write(
            "There are not enough other confirmed primes with complete windows to perform a similarity search."
        )

    else:
        match_count = int(
            st.select_slider(
                "Number of closest shadows to inspect",
                options=[
                    5,
                    8,
                    10,
                    12,
                    15,
                ],
                value=8,
            )
        )

        top_matches = matches[
            :match_count
        ]

        strongest_match = top_matches[0]
        same_mod_30 = sum(
            match.residue_mod_30
            == target_prime % 30
            for match in top_matches
        )

        similarity_metric_1, similarity_metric_2, similarity_metric_3 = st.columns(3)

        similarity_metric_1.metric(
            "Best deeper match",
            f"Prime {strongest_match.prime:,}",
            border=True,
        )

        similarity_metric_2.metric(
            "Deeper exact match",
            f"{strongest_match.deep_similarity:.1%}",
            border=True,
        )

        similarity_metric_3.metric(
            "Top matches sharing target mod 30 lane",
            f"{same_mod_30} of {match_count}",
            border=True,
            help=(
                "This helps reveal whether a similarity result is still strongly tied to the familiar modulo 30 wheel."
            ),
        )

        comparison_shadows = [
            target_shadow
        ]

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
                    f"Prime {target_prime:,} and its closest deeper shadow matches"
                ),
            ),
            width="stretch",
            config={
                "displaylogo": False,
            },
            key="prime_shadow_matches",
        )

        match_rows = [
            {
                "Prime": match.prime,
                "Distance from target": match.distance,
                "Prime mod 30": match.residue_mod_30,
                "Full shadow match": f"{match.full_similarity:.1%}",
                "Beyond 2, 3, 5 match": f"{match.deep_similarity:.1%}",
                "Deep positions compared": match.deep_positions_compared,
            }
            for match in top_matches
        ]

        with st.expander(
            "Show exact similarity results",
            expanded=False,
        ):
            st.dataframe(
                match_rows,
                width="stretch",
                hide_index=True,
            )

        st.warning(
            "A high shadow similarity is an observation, not evidence of a new prime law. "
            "Modular arithmetic creates recurring structure automatically. The useful question is whether a pattern persists after obvious structure is controlled for and across larger independent ranges."
        )


with st.container(border=True):
    st.subheader("4. What could become interesting")

    st.write(
        "This first version gives us a new coordinate system for primes: local sieve environment rather than numerical location. "
        "The next experiments can test whether shadow families correlate with prime gaps, twin primes, residue classes, or unusually large empty intervals."
    )

    st.markdown(
        """
**Good signs to investigate later**

1. Distant primes remain unusually similar after the 2, 3, and 5 structure is removed.
2. Similar shadow families repeatedly share unusual gap behavior.
3. A pattern survives changes in shadow radius and filter depth.
4. The same effect appears in independent number ranges rather than only one selected interval.
        """
    )
