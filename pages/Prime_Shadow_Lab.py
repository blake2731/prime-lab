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


def plain_shadow_state(code: int) -> str:
    """Translate a shadow state into newcomer friendly language."""

    if code == TARGET_CODE:
        return "CENTER PRIME"

    if code == CONFIRMED_CODE:
        return "PRIME"

    if code == UNRESOLVED_CODE:
        return "?"

    if code == NON_CANDIDATE_CODE:
        return "not a candidate"

    return str(code)


def plain_shadow_explanation(code: int) -> str:
    """Explain exactly what one shadow code means."""

    if code == TARGET_CODE:
        return "This is the center prime. It survived every applied filter."

    if code == CONFIRMED_CODE:
        return "This nearby number also survived and is mathematically confirmed prime."

    if code == UNRESOLVED_CODE:
        return "No applied filter has eliminated this number yet, but it is not proven prime."

    if code == NON_CANDIDATE_CODE:
        return "This number was never a valid prime candidate."

    return (
        f"Prime {code} was the first filter to prove this number composite, "
        "so it was the first prime to yank it out of prime candidacy."
    )


st.set_page_config(
    page_title="Prime Shadow Lab",
    page_icon="∴",
    layout="wide",
)


st.title("Prime Shadow Lab")
st.caption(
    "See a prime as the survivor inside a neighborhood where other numbers are being eliminated from prime candidacy."
)

st.info(
    "The simplest way to think about a prime shadow: every integer starts as a possible prime. "
    "As we test divisibility by 2, 3, 5, 7, and later primes, composite numbers get yanked out of prime candidacy. "
    "A shadow records which prime filter got each nearby number first. The center prime is the survivor."
)

with st.expander(
    "Why this is useful",
    expanded=True,
):
    st.write(
        "Ordinary prime plots mostly tell us where primes are. A shadow tells us what arithmetic environment surrounds one prime. "
        "For example, if a nearby number is labeled 7, that means 7 was the first applied prime that proved it composite."
    )

    st.code(
        "Integer     49   50   51   52   [53]   54   55   56   57   58   59\n"
        "First yank   7    2    3    2     P      2    5    2    3    2     P"
    )

    st.write(
        "Read that as: 49 lost prime candidacy to 7, 50 to 2, 51 to 3, 52 to 2, while 53 survived as prime. "
        "That sequence of eliminations is the local shadow around 53."
    )

    st.write(
        "Once we can describe one prime this way, we can ask whether distant primes live inside similar elimination environments, "
        "or whether certain shadow patterns tend to appear before twin primes, large gaps, or other interesting prime behavior."
    )


with st.container(border=True):
    st.subheader("1. Choose the experiment")
    st.caption(
        "For similarity work, Prime Shadow Lab uses only center primes whose entire shadow window lies inside both the selected range and the mathematically proven region. "
        "That prevents boundary effects and unresolved candidates from creating fake differences between fingerprints."
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

proven_window_end = min(
    range_end,
    frontier - 1,
)

eligible_mask = (
    (confirmed_values - radius >= range_start)
    & (
        confirmed_values + radius
        <= proven_window_end
    )
)

eligible_targets = confirmed_values[
    eligible_mask
]


if len(eligible_targets) == 0:
    st.warning(
        "There are no confirmed primes with a complete fully proven shadow window at this filter stage. Apply more filters, reduce the radius, or widen the range."
    )
    st.stop()


midpoint = (
    range_start
    + proven_window_end
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
                "Only confirmed primes whose complete shadow window is already mathematically resolved are offered here."
            ),
        )
    )

with control_right:
    st.metric(
        "Fully proven region available for shadows",
        f"{range_start:,} to {proven_window_end:,}",
        border=True,
        help=(
            f"The current proof frontier is n < {frontier:,}. Shadow comparison stays entirely below it."
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
    st.subheader("2. See what yanked the neighboring numbers out of prime candidacy")

    st.write(
        f"We are centering the view on confirmed prime **{target_prime:,}**. "
        f"Every position from **-{radius}** through **+{radius}** asks the same question: "
        "what happened to the integer at this distance from the center prime?"
    )

    st.info(
        "A number inside a composite cell is not the composite itself. It is the first prime filter that proved that neighbor composite. "
        "So a cell labeled 7 means: 7 was the first prime that yanked that neighbor out of prime candidacy."
    )

    metric_1, metric_2, metric_3, metric_4, metric_5 = st.columns(5)

    metric_1.metric(
        "Numbers in the shadow",
        f"{2 * radius + 1:,}",
        border=True,
    )

    metric_2.metric(
        "Neighbors proven composite",
        f"{target_counts['filtered_composites']:,}",
        border=True,
    )

    metric_3.metric(
        "Nearby primes that survived",
        f"{target_counts['confirmed_neighbors']:,}",
        border=True,
    )

    metric_4.metric(
        "Previous prime is this far away",
        (
            f"{left_gap:,}"
            if left_gap is not None
            else "Boundary"
        ),
        border=True,
    )

    metric_5.metric(
        "Next prime is this far away",
        (
            f"{right_gap:,}"
            if right_gap is not None
            else "Boundary"
        ),
        border=True,
    )

    center_index = target_shadow.offsets.index(0)
    example_start = max(
        0,
        center_index - 4,
    )
    example_end = min(
        len(target_shadow.offsets),
        center_index + 7,
    )

    example_rows = []

    for offset, value, code in zip(
        target_shadow.offsets[
            example_start:example_end
        ],
        target_shadow.values[
            example_start:example_end
        ],
        target_shadow.state_codes[
            example_start:example_end
        ],
        strict=True,
    ):
        example_rows.append(
            {
                "Offset": f"{offset:+d}",
                "Integer": value,
                "Shadow label": plain_shadow_state(code),
                "What it means": plain_shadow_explanation(code),
            }
        )

    st.markdown("**Read a small slice before reading the full shadow**")
    st.dataframe(
        example_rows,
        width="stretch",
        hide_index=True,
    )

    st.caption(
        "The Shadow label column is exactly what the colors below encode. P means a confirmed prime. A number such as 2, 3, 5, or 7 is the first prime filter that eliminated that neighbor."
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
        "The dark center line is the target prime. Moving left or right means moving the same number of integers away from that prime. "
        "For composite cells, color identifies the first applied prime divisor that eliminated that integer from prime candidacy."
    )

    higher_shadow_share = (
        target_counts["higher_prime_shadows"]
        / max(
            target_counts["filtered_composites"],
            1,
        )
    )

    st.write(
        f"In this window, **{target_counts['higher_prime_shadows']:,}** composite neighbors were not caught by 2, 3, or 5 and needed a larger prime filter to eliminate them. "
        f"That is **{higher_shadow_share:.1%}** of the resolved composite neighbors. These positions are especially interesting because they sit beyond the strongest repeating wheel structure."
    )


with st.container(border=True):
    st.subheader("3. Ask whether distant primes live in similar neighborhoods")

    st.write(
        "Now that one shadow is readable, comparison has a simple meaning: "
        "do two distant primes have nearby numbers yanked out of prime candidacy by the same primes at the same relative positions?"
    )

    st.write(
        "A raw comparison is heavily influenced by the repeating effects of 2, 3, and 5. "
        "Prime Shadow Lab therefore also computes a deeper comparison that ignores positions where either shadow is first eliminated by 2, 3, or 5."
    )

    st.caption(
        "This deeper score is exploratory. A high percentage is not automatically strong evidence because the number of remaining positions matters too. "
        "The exact table below always reports how many positions were actually compared."
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

        total_noncenter_positions = 2 * radius
        deep_coverage = (
            strongest_match.deep_positions_compared
            / total_noncenter_positions
        )

        similarity_metric_1, similarity_metric_2, similarity_metric_3, similarity_metric_4 = st.columns(4)

        similarity_metric_1.metric(
            "Closest deeper shadow",
            f"Prime {strongest_match.prime:,}",
            border=True,
        )

        similarity_metric_2.metric(
            "Agreement on compared positions",
            f"{strongest_match.deep_similarity:.1%}",
            border=True,
        )

        similarity_metric_3.metric(
            "Positions actually compared",
            (
                f"{strongest_match.deep_positions_compared} of "
                f"{total_noncenter_positions}"
            ),
            border=True,
        )

        similarity_metric_4.metric(
            "Informative coverage",
            f"{deep_coverage:.1%}",
            border=True,
            help=(
                "Coverage is the share of noncenter positions left after removing positions dominated by 2, 3, and 5. A high agreement with very low coverage should be treated cautiously."
            ),
        )

        if deep_coverage < 0.25:
            st.warning(
                "The best match is based on relatively few informative positions after removing the 2, 3, and 5 structure. "
                "Treat the agreement percentage as weak evidence until we replace this first similarity method with a stronger wheel normalized comparison."
            )

        else:
            st.info(
                f"Among the top {match_count} deeper matches, {same_mod_30} share the same modulo 30 lane as the center prime. "
                "That check helps us notice when familiar wheel structure may still be driving the result."
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
                "Full shadow agreement": f"{match.full_similarity:.1%}",
                "Agreement after ignoring 2, 3, 5": f"{match.deep_similarity:.1%}",
                "Positions actually compared": match.deep_positions_compared,
                "Coverage": (
                    f"{match.deep_positions_compared / total_noncenter_positions:.1%}"
                ),
            }
            for match in top_matches
        ]

        with st.expander(
            "Show the evidence behind the similarity scores",
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
    st.subheader("4. Why we are looking at shadows")

    st.write(
        "The point is not to make another decorative prime picture. A shadow turns each prime into a local arithmetic environment. "
        "Instead of only asking where a prime occurs, we can ask what sequence of divisibility constraints surrounds the survivor."
    )

    st.write(
        "For a large prime gap, this means we can inspect which primes collectively eliminated every number between the two surviving endpoints. "
        "For twin primes, we can ask whether their surrounding elimination environments have recurring features."
    )

    st.markdown(
        """
**Good signs to investigate later**

1. Distant primes remain unusually similar after the obvious 2, 3, and 5 structure is controlled for.
2. Similar shadow families repeatedly share unusual gap behavior.
3. A pattern survives changes in shadow radius and filter depth.
4. The same effect appears in independent number ranges rather than only one selected interval.
        """
    )
