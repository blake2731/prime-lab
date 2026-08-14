import numpy as np
import streamlit as st

from prime_lab.certification import (
    certification_frontier,
    confirmed_prime_mask,
)
from prime_lab.filter_efficiency import (
    filter_efficiency_steps,
)
from prime_lab.filters import filter_candidates
from prime_lab.residue_analysis import residue_class_summaries
from ui.candidate_grid import build_candidate_figure
from ui.filter_efficiency import build_filter_efficiency_figure
from ui.residue_structure import build_residue_figure
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
    37,
    41,
    43,
    47,
    53,
    59,
    61,
    67,
)

SQUARE_VIEW = "Square grid"
CUSTOM_WIDTH_VIEW = "Custom width grid"
ACTIVE_PRIME_VIEW = "Active prime alignment"
MODULO_30_VIEW = "Modulo 30 residue lanes"


st.set_page_config(
    page_title="Prime Lab",
    page_icon="∴",
    layout="wide",
)


st.title("Prime Lab")
st.caption(
    "Explore how prime candidates are eliminated, confirmed, and reorganized under different mathematical views."
)

st.info(
    "Start here: choose a number range, choose the highest prime filter to apply, then choose how to view the same mathematical state. "
    "Changing the view never changes which numbers survive or which numbers are confirmed prime. It only changes how the same information is arranged."
)

with st.expander(
    "How Prime Lab works",
    expanded=False,
):
    st.markdown(
        """
**1. Begin with candidates.** Every integer greater than 1 starts as a possible prime.

**2. Apply prime filters.** If you choose **Prime 7**, Prime Lab applies filters 2, 3, 5, and 7 in order. A composite is assigned to the first prime that proves it composite.

**3. Separate survivors from proven primes.** A survivor is still a candidate. A survivor becomes **confirmed prime** only when the filters already tested are enough to rule out every possible prime divisor up to its square root.

**4. Change the projection.** Square, custom width, active prime alignment, and modulo 30 all show the same numbers in different coordinate systems. A pattern that survives several projections is more interesting than one that appears in only one layout.
        """
    )

    st.markdown(
        "**Color key:** teal = confirmed prime, blue = unresolved survivor, amber = first eliminated by the currently selected prime, gray = eliminated earlier or not a prime candidate."
    )


with st.container(border=True):
    st.subheader("1. Choose the experiment")
    st.caption(
        "The range chooses which integers are visible. The filter control chooses how much divisibility testing has been completed."
    )

    col_start, col_end, col_filter = st.columns([1, 1, 1.25])

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
            value=500,
            step=1,
            help="The last integer included in the experiment.",
        )

    with col_filter:
        filter_options = [
            None,
            *FILTER_PRIMES,
        ]

        active_prime = st.selectbox(
            "Apply prime filters through",
            filter_options,
            index=0,
            format_func=lambda value: (
                "No filters yet" if value is None else f"Prime {value}"
            ),
            help=(
                "Choosing Prime 7 applies the complete sequence 2, 3, 5, and 7. "
                "Prime Lab never skips an earlier prime filter."
            ),
        )


if range_end < range_start:
    st.error("Range end must be greater than or equal to range start.")
    st.stop()


range_size = range_end - range_start + 1


if range_size > 5000:
    st.warning("This visual build is currently limited to 5,000 visible integers.")
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

confirmed = confirmed_prime_mask(
    values,
    survives,
    applied_primes,
)

frontier = certification_frontier(applied_primes)
confirmed_count = int(np.count_nonzero(confirmed))
initial_candidates = int(np.count_nonzero(values >= 2))
survivor_count = int(np.count_nonzero(survives))
eliminated_count = initial_candidates - survivor_count


if active_prime is None:
    newly_eliminated = 0
else:
    newly_eliminated = int(np.count_nonzero(eliminated_by == active_prime))


survival_rate = survivor_count / initial_candidates if initial_candidates else 0


metric_1, metric_2, metric_3, metric_4, metric_5 = st.columns(5)

metric_1.metric(
    "Integers shown",
    f"{range_size:,}",
    border=True,
)

metric_2.metric(
    "Still surviving",
    f"{survivor_count:,}",
    border=True,
)

metric_3.metric(
    "Confirmed primes",
    f"{confirmed_count:,}",
    border=True,
)

metric_4.metric(
    "Eliminated",
    f"{eliminated_count:,}",
    border=True,
)

metric_5.metric(
    "Survival rate",
    f"{survival_rate:.2%}",
    border=True,
)

st.caption(
    "Still surviving includes both confirmed primes and unresolved candidates. Confirmed primes are the subset that the current filter sequence has already proven prime."
)


with st.container(border=True):
    st.subheader("2. Choose how to view the same numbers")
    st.caption(
        "A projection changes the geometry of the display, not the underlying mathematics. Use different projections to test whether a visible pattern is arithmetic or just a consequence of layout."
    )

    square_width = max(
        10,
        int(np.ceil(np.sqrt(range_size))),
    )

    projection_options = [
        SQUARE_VIEW,
        CUSTOM_WIDTH_VIEW,
    ]

    if active_prime is not None:
        projection_options.append(
            ACTIVE_PRIME_VIEW
        )

    projection_options.append(
        MODULO_30_VIEW
    )

    projection_control, projection_detail = st.columns(
        [1, 2]
    )

    with projection_control:
        projection = st.selectbox(
            "View",
            projection_options,
            key="projection_mode",
            help="Every option rearranges the same experiment state in a different way.",
        )

    projection_grid_width = None

    with projection_detail:
        if projection == SQUARE_VIEW:
            st.metric(
                "Automatic row width",
                f"{square_width:,}",
                border=True,
            )

        elif projection == CUSTOM_WIDTH_VIEW:
            maximum_width = max(
                2,
                min(
                    250,
                    max(range_size, 2),
                ),
            )

            default_width = min(
                square_width,
                maximum_width,
            )

            projection_grid_width = int(
                st.number_input(
                    "Integers per row",
                    min_value=2,
                    max_value=maximum_width,
                    value=default_width,
                    step=1,
                    key="fixed_projection_width",
                    help=(
                        "Changing only this width is a useful test. If a pattern disappears at a nearby width, it may be caused by the projection rather than the integers."
                    ),
                )
            )

        elif projection == ACTIVE_PRIME_VIEW:
            projection_grid_width = int(
                active_prime
            )

            st.metric(
                "Integers per row",
                f"{projection_grid_width:,}",
                border=True,
            )

        else:
            st.metric(
                "Remainder classes",
                "30",
                border=True,
            )

    if projection == SQUARE_VIEW:
        st.markdown("**What this view means**")
        st.write(
            f"Prime Lab places consecutive integers into rows of {square_width:,}, producing a compact field that is as close to square as practical. "
            "This is good for seeing overall density, but the row width itself can create visual alignments."
        )

    elif projection == CUSTOM_WIDTH_VIEW:
        st.markdown("**What this view means**")
        st.write(
            f"Prime Lab places exactly {projection_grid_width:,} consecutive integers in each row. "
            "Try nearby widths such as one less or one more to see whether a pattern survives the change in geometry."
        )

    elif projection == ACTIVE_PRIME_VIEW:
        st.markdown("**What this view means**")
        st.write(
            f"Each row contains exactly {active_prime} integers. Values with the same remainder after division by {active_prime} line up vertically. "
            f"This makes the arithmetic structure of the active prime {active_prime} much easier to see."
        )

    else:
        st.markdown("**What this view means**")
        st.write(
            "Instead of wrapping integers into ordinary rows, this view sorts every integer into one of 30 horizontal lanes according to its remainder after division by 30."
        )
        st.caption(
            "Example: 31 = 30 × 1 + 1 and 61 = 30 × 2 + 1, so both appear in remainder lane 1. The horizontal direction moves through successive blocks of 30."
        )

        if active_prime is None or active_prime < 5:
            st.info(
                "This view becomes most informative after filters 2, 3, and 5 have all been applied. Choose Prime 5 or higher to reveal the eight lanes that can contain primes greater than 5."
            )
        else:
            st.success(
                "After filters 2, 3, and 5, every prime greater than 5 must lie in one of these eight remainder lanes: 1, 7, 11, 13, 17, 19, 23, or 29."
            )

    if projection == MODULO_30_VIEW:
        projection_figure = build_residue_figure(
            values,
            survives,
            eliminated_by,
            confirmed,
            active_prime,
        )

        chart_key = "projection_modulo_30"

    else:
        if applied_primes:
            projection_figure = build_sieve_animation(
                range_start,
                range_end,
                applied_primes,
                grid_width=projection_grid_width,
            )
        else:
            projection_figure = build_candidate_figure(
                values,
                survives,
                eliminated_by,
                active_prime,
                confirmed,
                grid_width=projection_grid_width,
            )

        chart_key = "projection_candidate_grid"

    st.plotly_chart(
        projection_figure,
        width="stretch",
        config={
            "displaylogo": False,
        },
        key=chart_key,
    )

    if projection == MODULO_30_VIEW:
        st.caption(
            "The right hand bars summarize how many surviving candidates and confirmed primes occupy each remainder lane. The modulo 30 view is intentionally static so the structure can be inspected without animation redraws."
        )

        summaries = residue_class_summaries(
            values,
            survives,
            eliminated_by,
            confirmed,
            active_prime,
            modulus=30,
        )

        eligible_summaries = tuple(
            summary
            for summary in summaries
            if summary.prime_eligible
        )

        confirmed_above_five = int(
            np.count_nonzero(
                confirmed
                & (values > 5)
            )
        )

        if confirmed_above_five:
            confirmed_counts = [
                summary.confirmed
                for summary in eligible_summaries
            ]

            minimum_confirmed = min(
                confirmed_counts
            )

            maximum_confirmed = max(
                confirmed_counts
            )

            busiest_summary = max(
                eligible_summaries,
                key=lambda summary: (
                    summary.confirmed,
                    -summary.residue,
                ),
            )

            busiest_label = (
                f"Lane {busiest_summary.residue} with "
                f"{busiest_summary.confirmed:,}"
            )

            spread_label = (
                f"{minimum_confirmed:,} to {maximum_confirmed:,}"
            )

        else:
            busiest_label = "Not enough confirmed primes"
            spread_label = "Not enough confirmed primes"

        st.markdown("**What the modulo 30 summary is measuring**")

        residue_metric_1, residue_metric_2, residue_metric_3, residue_metric_4 = st.columns(4)

        residue_metric_1.metric(
            "Prime eligible lanes",
            "8 of 30",
            border=True,
        )

        residue_metric_2.metric(
            "Confirmed primes above 5",
            f"{confirmed_above_five:,}",
            border=True,
        )

        residue_metric_3.metric(
            "Most populated confirmed lane",
            busiest_label,
            border=True,
        )

        residue_metric_4.metric(
            "Confirmed counts across lanes",
            spread_label,
            border=True,
        )

        with st.expander(
            "Show exact counts for the eight prime eligible lanes",
            expanded=False,
        ):
            st.write(
                "Each row below represents one remainder after division by 30. These are the only eight remainders available to primes greater than 5."
            )

            residue_rows = [
                {
                    "Remainder": summary.residue,
                    "Confirmed primes": summary.confirmed,
                    "Unresolved survivors": summary.unresolved,
                    "First removed by current prime": summary.current_removed,
                }
                for summary in eligible_summaries
            ]

            st.dataframe(
                residue_rows,
                width="stretch",
                hide_index=True,
            )

            st.caption(
                "The small primes 2, 3, and 5 are special exceptions because they divide 30 themselves. Counts here describe only the selected finite range and should not be interpreted as a claim that one lane is permanently favored."
            )


with st.container(border=True):
    st.subheader("3. Measure how much work each prime filter performs")
    st.caption(
        "A filter gets credit only for composites that survived every earlier filter and are eliminated for the first time by that prime."
    )

    if not applied_primes:
        st.write(
            "Choose at least Prime 2 above to begin measuring filter efficiency."
        )

    else:
        efficiency_steps = filter_efficiency_steps(
            range_start,
            range_end,
            applied_primes,
        )

        current_efficiency = efficiency_steps[-1]
        strongest_step = max(
            efficiency_steps,
            key=lambda step: step.removed,
        )

        efficiency_metric_1, efficiency_metric_2, efficiency_metric_3 = st.columns(3)

        efficiency_metric_1.metric(
            "New composites removed by current prime",
            f"{current_efficiency.removed:,}",
            border=True,
        )

        efficiency_metric_2.metric(
            "Share of incoming candidates removed",
            f"{current_efficiency.marginal_removal_rate:.2%}",
            border=True,
        )

        efficiency_metric_3.metric(
            "Most productive filter so far",
            f"Prime {strongest_step.prime} with {strongest_step.removed:,}",
            border=True,
        )

        efficiency_figure = build_filter_efficiency_figure(
            range_start,
            range_end,
            applied_primes,
        )

        st.plotly_chart(
            efficiency_figure,
            width="stretch",
            config={
                "displaylogo": False,
            },
            key="filter_efficiency",
        )

        st.caption(
            "Amber bars count newly eliminated composites. The blue line shows the fraction of candidates reaching each filter that it removes. The teal line shows what fraction of the original candidate population remains after that filter."
        )


with st.container(border=True):
    st.subheader("4. Understand the current filter state")

    if active_prime is None:
        st.write(
            "No divisibility filters have been applied yet. Every integer greater than 1 is still being treated as a candidate."
        )

    else:
        detail_left, detail_right = st.columns([2, 1])

        with detail_left:
            st.write(
                f"Filtering through Prime {active_prime} means every prime filter from 2 through {active_prime} in the sequence has been applied."
            )

            st.code(f"current rule: n % {active_prime} == 0")

            if frontier is not None:
                st.write(
                    f"The current proof frontier is **n < {frontier:,}**. Any surviving candidate below that frontier is confirmed prime because every possible prime divisor up to its square root has already been tested."
                )

            st.markdown(
                "**Read the colors:** teal is confirmed prime, blue is still unresolved, amber was first eliminated by the currently selected prime, and gray was eliminated earlier or was never a valid prime candidate."
            )

        with detail_right:
            st.metric(
                f"First removed by Prime {active_prime}",
                f"{newly_eliminated:,}",
                border=True,
            )

            st.metric(
                "Confirmed primes",
                f"{confirmed_count:,}",
                border=True,
            )

    st.caption(
        "Prime Lab distinguishes surviving from proven. Surviving only means no applied filter has eliminated the number yet. Confirmed means the applied filters are already sufficient to prove primality."
    )
