import numpy as np
import pandas as pd
import streamlit as st

from prime_lab.certification import certification_frontier, confirmed_prime_mask
from prime_lab.filter_efficiency import filter_efficiency_steps
from prime_lab.filters import filter_candidates
from prime_lab.residue_analysis import residue_class_summaries
from ui.candidate_grid import build_candidate_figure
from ui.filter_efficiency import build_filter_efficiency_figure
from ui.residue_structure import build_residue_figure


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
ACTIVE_PRIME_VIEW = "Selected prime alignment"
MODULO_30_VIEW = "Modulo 30 residue lanes"
MAX_VISIBLE_INTEGERS = 5_000


st.set_page_config(
    page_title="Prime Lab",
    page_icon="∴",
    layout="wide",
)

st.title("Prime Lab")
st.caption(
    "Inspect the sieve state directly: which integers have been resolved as composite, which remain candidates, and which survivors are already proven prime."
)

st.info(
    "Prime Lab is the baseline experiment for the project. It keeps the mathematical state static while controls change the range, sieve depth, or projection. "
    "Animated divisibility is handled separately in Kinetic Sieve Lab so this page remains suitable for exact inspection and comparison."
)

with st.expander("State model and terminology", expanded=True):
    st.markdown(
        """
**Candidate.** Every integer at least 2 begins as a possible prime.

**Resolved composite.** A candidate is resolved when an applied prime divides it. The first eliminating prime is the smallest applied prime divisor that proves the number composite.

**Unresolved candidate.** No applied filter divides the number, but the current filter depth is not yet sufficient to prove primality.

**Confirmed prime.** A surviving candidate is confirmed only when the complete applied prime sequence reaches far enough to test every possible prime divisor through its square root.

**Projection.** A projection rearranges the same state geometrically. It never changes which integers are composite, unresolved, or confirmed prime.
        """
    )
    st.markdown(
        "**Color key:** teal = confirmed prime, blue = unresolved candidate, amber = first eliminated by the selected final filter, gray = resolved earlier or not a prime candidate."
    )


with st.container(border=True):
    st.subheader("1. Define the sieve state")
    st.caption(
        "Select a finite integer range and the deepest prime filter to apply. Filters are always applied as a complete ascending sequence beginning with 2."
    )

    col_start, col_end, col_filter = st.columns([1, 1, 1.35])

    with col_start:
        range_start = int(
            st.number_input(
                "Range start",
                min_value=1,
                value=1,
                step=1,
                help="First integer included in the experiment.",
            )
        )

    with col_end:
        range_end = int(
            st.number_input(
                "Range end",
                min_value=2,
                value=300,
                step=1,
                help="Last integer included in the experiment.",
            )
        )

    with col_filter:
        filter_options = [None, *FILTER_PRIMES]
        active_prime = st.selectbox(
            "Apply prime filters through",
            filter_options,
            index=3,
            format_func=lambda value: "No filters" if value is None else f"Prime {value}",
            help=(
                "Selecting Prime 7 applies 2, 3, 5, and 7 in order. The selected prime is the final applied filter, not the only filter."
            ),
        )

if range_end < range_start:
    st.error("Range end must be greater than or equal to range start.")
    st.stop()

range_size = range_end - range_start + 1
if range_size > MAX_VISIBLE_INTEGERS:
    st.warning(
        f"Prime Lab currently limits the inspection field to {MAX_VISIBLE_INTEGERS:,} integers so every displayed state remains interactive."
    )
    st.stop()

if active_prime is None:
    applied_primes: tuple[int, ...] = ()
else:
    active_index = FILTER_PRIMES.index(active_prime)
    applied_primes = FILTER_PRIMES[: active_index + 1]

values, survives, eliminated_by = filter_candidates(
    range_start,
    range_end,
    applied_primes,
)
confirmed = confirmed_prime_mask(values, survives, applied_primes)
frontier = certification_frontier(applied_primes)

candidate_mask = values >= 2
unresolved = survives & candidate_mask & ~confirmed
initial_candidates = int(np.count_nonzero(candidate_mask))
survivor_count = int(np.count_nonzero(survives & candidate_mask))
confirmed_count = int(np.count_nonzero(confirmed))
unresolved_count = int(np.count_nonzero(unresolved))
eliminated_count = initial_candidates - survivor_count
newly_eliminated = (
    int(np.count_nonzero(eliminated_by == active_prime))
    if active_prime is not None
    else 0
)

metric_1, metric_2, metric_3, metric_4, metric_5 = st.columns(5)
metric_1.metric("Prime candidates", f"{initial_candidates:,}", border=True)
metric_2.metric("Resolved composites", f"{eliminated_count:,}", border=True)
metric_3.metric("Unresolved candidates", f"{unresolved_count:,}", border=True)
metric_4.metric("Confirmed primes", f"{confirmed_count:,}", border=True)
metric_5.metric(
    "Proof frontier",
    "Not established" if frontier is None else f"n < {frontier:,}",
    border=True,
)

if active_prime is None:
    st.caption(
        "No prime filters are active. Every integer at least 2 remains an unresolved candidate, so no prime has yet been certified by this experiment."
    )
else:
    coverage_end = min(range_end, frontier - 1) if frontier is not None else None
    st.caption(
        f"Filters applied: {', '.join(str(prime) for prime in applied_primes)}. "
        f"Prime {active_prime} uniquely resolves {newly_eliminated:,} candidates that survived every earlier applied filter. "
        + (
            f"Within the visible range, surviving candidates through {coverage_end:,} are mathematically confirmed prime."
            if coverage_end is not None and coverage_end >= range_start
            else "The current proof frontier lies before the selected visible range."
        )
    )


with st.container(border=True):
    st.subheader("2. Inspect one projection")
    st.caption(
        "The field below is static. Changing the projection changes only where cells are placed, allowing geometric artifacts to be separated from arithmetic structure."
    )

    square_width = max(8, int(np.ceil(np.sqrt(range_size))))
    projection_options = [SQUARE_VIEW, CUSTOM_WIDTH_VIEW]
    if active_prime is not None:
        projection_options.append(ACTIVE_PRIME_VIEW)
    projection_options.append(MODULO_30_VIEW)

    projection_control, projection_detail = st.columns([1, 2])
    with projection_control:
        projection = st.selectbox(
            "Projection",
            projection_options,
            key="projection_mode",
            help="Each option shows the same candidate state in a different coordinate system.",
        )

    projection_grid_width: int | None = None
    with projection_detail:
        if projection == SQUARE_VIEW:
            st.metric("Integers per row", f"{square_width:,}", border=True)
        elif projection == CUSTOM_WIDTH_VIEW:
            maximum_width = max(2, min(250, range_size))
            projection_grid_width = int(
                st.number_input(
                    "Integers per row",
                    min_value=2,
                    max_value=maximum_width,
                    value=min(square_width, maximum_width),
                    step=1,
                    key="fixed_projection_width",
                    help="Changing only this width tests whether an apparent alignment is caused by the display geometry.",
                )
            )
        elif projection == ACTIVE_PRIME_VIEW:
            projection_grid_width = int(active_prime)
            st.metric("Integers per row", f"{projection_grid_width:,}", border=True)
        else:
            st.metric("Remainder classes", "30", border=True)

    if projection == SQUARE_VIEW:
        st.write(
            f"Consecutive integers are wrapped into rows of {square_width:,}. This compact view is useful for density, but alignments can be produced by the chosen row width."
        )
    elif projection == CUSTOM_WIDTH_VIEW:
        st.write(
            f"Exactly {projection_grid_width:,} integers are placed in each row. Nearby widths provide a direct control test for projection dependent patterns."
        )
    elif projection == ACTIVE_PRIME_VIEW:
        st.write(
            f"Rows contain {active_prime} integers. Equal remainders modulo {active_prime} align vertically, exposing the periodic structure of the selected prime filter."
        )
    else:
        st.write(
            "Integers are placed into 30 remainder lanes. After filters 2, 3, and 5, primes greater than 5 can occur only in lanes 1, 7, 11, 13, 17, 19, 23, and 29."
        )
        if active_prime is None or active_prime < 5:
            st.info(
                "Apply filters through Prime 5 or deeper to expose the complete modulo 30 prime eligible residue structure."
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
        config={"displaylogo": False},
        key=chart_key,
    )

    if range_size <= 400 and projection != MODULO_30_VIEW:
        st.caption("Integer labels are shown directly because the visible field contains at most 400 values.")
    elif projection != MODULO_30_VIEW:
        st.caption("The field is too dense for direct labels; hover over a cell to inspect the integer and exact state.")

    if projection == MODULO_30_VIEW:
        summaries = residue_class_summaries(
            values,
            survives,
            eliminated_by,
            confirmed,
            active_prime,
            modulus=30,
        )
        eligible_summaries = tuple(summary for summary in summaries if summary.prime_eligible)
        confirmed_above_five = int(np.count_nonzero(confirmed & (values > 5)))

        if confirmed_above_five:
            busiest_summary = max(
                eligible_summaries,
                key=lambda summary: (summary.confirmed, -summary.residue),
            )
            confirmed_counts = [summary.confirmed for summary in eligible_summaries]
            busiest_label = f"Lane {busiest_summary.residue} · {busiest_summary.confirmed:,}"
            spread_label = f"{min(confirmed_counts):,} to {max(confirmed_counts):,}"
        else:
            busiest_label = "No confirmed sample"
            spread_label = "No confirmed sample"

        residue_metric_1, residue_metric_2, residue_metric_3, residue_metric_4 = st.columns(4)
        residue_metric_1.metric("Prime eligible lanes", "8 of 30", border=True)
        residue_metric_2.metric("Confirmed primes above 5", f"{confirmed_above_five:,}", border=True)
        residue_metric_3.metric("Most populated lane", busiest_label, border=True)
        residue_metric_4.metric("Confirmed count range", spread_label, border=True)

        with st.expander("Exact modulo 30 lane counts", expanded=False):
            residue_rows = [
                {
                    "Remainder": summary.residue,
                    "Confirmed primes": summary.confirmed,
                    "Unresolved candidates": summary.unresolved,
                    "First eliminated by selected filter": summary.current_removed,
                }
                for summary in eligible_summaries
            ]
            st.dataframe(residue_rows, width="stretch", hide_index=True)
            st.caption(
                "These counts describe only the selected finite range. A larger count in one residue lane is not evidence that the lane is permanently favored."
            )


with st.container(border=True):
    st.subheader("3. Measure filter contribution")
    st.caption(
        "Each prime receives credit only for candidates that survived all earlier filters and are first resolved by that prime."
    )

    if not applied_primes:
        st.write("Apply at least Prime 2 to measure filter contribution.")
    else:
        efficiency_steps = filter_efficiency_steps(
            range_start,
            range_end,
            applied_primes,
        )
        current_efficiency = efficiency_steps[-1]
        strongest_step = max(efficiency_steps, key=lambda step: step.removed)

        efficiency_metric_1, efficiency_metric_2, efficiency_metric_3 = st.columns(3)
        efficiency_metric_1.metric(
            f"Unique removals by Prime {active_prime}",
            f"{current_efficiency.removed:,}",
            border=True,
        )
        efficiency_metric_2.metric(
            "Marginal removal rate",
            f"{current_efficiency.marginal_removal_rate:.2%}",
            border=True,
        )
        efficiency_metric_3.metric(
            "Largest unique contribution",
            f"Prime {strongest_step.prime} · {strongest_step.removed:,}",
            border=True,
        )

        st.plotly_chart(
            build_filter_efficiency_figure(range_start, range_end, applied_primes),
            width="stretch",
            config={"displaylogo": False},
            key="filter_efficiency",
        )

        efficiency_rows = [
            {
                "Prime filter": step.prime,
                "Candidates before": step.candidates_before,
                "Unique composites removed": step.removed,
                "Candidates after": step.candidates_after,
                "Marginal removal rate": step.marginal_removal_rate,
                "Cumulative survival rate": step.cumulative_survival_rate,
            }
            for step in efficiency_steps
        ]
        with st.expander("Exact filter contribution table", expanded=False):
            st.dataframe(
                pd.DataFrame(efficiency_rows),
                width="stretch",
                hide_index=True,
                column_config={
                    "Marginal removal rate": st.column_config.NumberColumn(format="%.4f"),
                    "Cumulative survival rate": st.column_config.NumberColumn(format="%.4f"),
                },
            )


with st.container(border=True):
    st.subheader("4. Inspect and export the exact state")
    st.caption(
        "The table is the nonvisual form of the experiment. It is useful for checking a suspicious cell, reproducing a result, or exporting the state for external analysis."
    )

    state_rows = []
    for index, value in enumerate(values):
        if value < 2:
            state = "Not a prime candidate"
        elif confirmed[index]:
            state = "Confirmed prime"
        elif survives[index]:
            state = "Unresolved candidate"
        else:
            state = "Resolved composite"

        first_eliminating_prime = int(eliminated_by[index]) if eliminated_by[index] > 0 else None
        state_rows.append(
            {
                "Integer": int(value),
                "State": state,
                "First eliminating prime": first_eliminating_prime,
                "First eliminated by selected filter": bool(
                    active_prime is not None and first_eliminating_prime == active_prime
                ),
            }
        )

    state_frame = pd.DataFrame(state_rows)
    table_col, export_col = st.columns([4, 1])
    with table_col:
        with st.expander("Exact integer state table", expanded=False):
            st.dataframe(state_frame, width="stretch", hide_index=True)
    with export_col:
        st.download_button(
            "Download state CSV",
            data=state_frame.to_csv(index=False).encode("utf-8"),
            file_name=f"prime_lab_state_{range_start}_{range_end}.csv",
            mime="text/csv",
            width="stretch",
        )


with st.expander("Methods and limits", expanded=False):
    st.markdown(
        f"""
**Certification rule.** If every prime through p has been applied and q is the next prime after p, every surviving candidate below q² is confirmed prime.

**Finite display.** The baseline page is limited to {MAX_VISIBLE_INTEGERS:,} visible integers. This is a visualization limit rather than a limit of prime arithmetic.

**Static by design.** Prime Lab displays the exact selected state without automatic playback. Kinetic Sieve Lab is the dedicated real time view of divisibility events.

**Projection control.** Square grids and custom row widths can create apparent alignments. Modulo based projections are arithmetic coordinate systems and should be distinguished from purely geometric wrapping.

**Interpretation.** A visible pattern is an observation. Any proposed relationship should be measured, compared against known modular structure, and reproduced on independent ranges before it is treated as evidence.
        """
    )
