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
DEFAULT_EXPERIMENT = {
    "start": 1,
    "end": 300,
    "active_prime": 5,
}


@st.cache_data(show_spinner=False)
def compute_sieve_state(
    start: int,
    end: int,
    applied_primes: tuple[int, ...],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, int | None]:
    """Compute one immutable sieve state for the baseline laboratory."""

    values, survives, eliminated_by = filter_candidates(
        start,
        end,
        applied_primes,
    )
    confirmed = confirmed_prime_mask(
        values,
        survives,
        applied_primes,
    )
    frontier = certification_frontier(applied_primes)
    return values, survives, eliminated_by, confirmed, frontier


def state_label(
    *,
    value: int,
    survives: bool,
    confirmed: bool,
    eliminated_by: int,
) -> str:
    """Return the project terminology for one integer state."""

    if value < 2:
        return "Not a prime candidate"
    if confirmed:
        return "Confirmed prime"
    if survives:
        return "Unresolved candidate"
    if eliminated_by > 0:
        return "Resolved composite"
    return "Not a prime candidate"


def experiment_token(
    start: int,
    end: int,
    active_prime: int | None,
) -> str:
    """Create a stable UI identity for one committed experiment state."""

    return f"{start}_{end}_{active_prime if active_prime is not None else 0}"


st.set_page_config(
    page_title="Prime Lab",
    page_icon="∴",
    layout="wide",
)

if "prime_lab_experiment" not in st.session_state:
    st.session_state["prime_lab_experiment"] = DEFAULT_EXPERIMENT.copy()

st.title("Prime Lab")
st.caption(
    "Build and inspect one exact sieve state, then test how the same arithmetic structure appears under different projections."
)

st.info(
    "Prime Lab is the baseline instrument for the project. It separates exact state inspection from animation: this page remains static and reproducible, while Kinetic Sieve Lab shows the same divisibility process in motion."
)

with st.expander("State model and terminology", expanded=False):
    st.markdown(
        """
**Candidate.** Every integer at least 2 begins as a possible prime.

**Resolved composite.** An applied prime divides the candidate. The first eliminating prime is the smallest applied prime divisor that proves it composite.

**Unresolved candidate.** No applied filter divides the number, but the current filter depth is not sufficient to prove primality.

**Confirmed prime.** A surviving candidate is confirmed only when the complete applied prime sequence tests every possible prime divisor through its square root.

**Projection.** A projection rearranges the same exact state. It never changes which integers are composite, unresolved, or confirmed prime.
        """
    )
    st.markdown(
        "**Color key:** teal = confirmed prime, blue = unresolved candidate, amber = first eliminated by the selected final filter, gray = resolved earlier or not a prime candidate."
    )


committed = st.session_state["prime_lab_experiment"]
filter_options = [None, *FILTER_PRIMES]

with st.container(border=True):
    st.subheader("1. Define the experiment")
    st.caption(
        "Changes are applied together. Editing a control does not rebuild the visualization until Apply experiment is selected."
    )

    with st.form("prime_lab_experiment_form", border=False):
        control_one, control_two, control_three = st.columns([1, 1, 1.35])

        with control_one:
            draft_start = int(
                st.number_input(
                    "Range start",
                    min_value=1,
                    value=int(committed["start"]),
                    step=1,
                    help="First integer included in the experiment.",
                )
            )

        with control_two:
            draft_end = int(
                st.number_input(
                    "Range end",
                    min_value=2,
                    value=int(committed["end"]),
                    step=1,
                    help=f"Last integer included in the experiment. At most {MAX_VISIBLE_INTEGERS:,} integers can be displayed at once.",
                )
            )

        with control_three:
            draft_active_prime = st.selectbox(
                "Apply prime filters through",
                filter_options,
                index=filter_options.index(committed["active_prime"]),
                format_func=lambda value: "No filters" if value is None else f"Prime {value}",
                help=(
                    "Selecting Prime 7 applies 2, 3, 5, and 7 in order. The selected prime is the final applied filter, not the only filter."
                ),
            )

        button_one, button_two, button_space = st.columns([1, 1, 4])
        with button_one:
            apply_experiment = st.form_submit_button(
                "Apply experiment",
                type="primary",
                width="stretch",
            )
        with button_two:
            reset_experiment = st.form_submit_button(
                "Reset starter view",
                width="stretch",
            )

    if reset_experiment:
        st.session_state["prime_lab_experiment"] = DEFAULT_EXPERIMENT.copy()
        committed = st.session_state["prime_lab_experiment"]
        st.rerun()

    if apply_experiment:
        proposed_size = draft_end - draft_start + 1
        if draft_end < draft_start:
            st.error("Range end must be greater than or equal to range start. The previous experiment remains active.")
        elif proposed_size > MAX_VISIBLE_INTEGERS:
            st.error(
                f"The baseline visual field is limited to {MAX_VISIBLE_INTEGERS:,} integers. The previous experiment remains active."
            )
        else:
            st.session_state["prime_lab_experiment"] = {
                "start": draft_start,
                "end": draft_end,
                "active_prime": draft_active_prime,
            }
            committed = st.session_state["prime_lab_experiment"]


range_start = int(committed["start"])
range_end = int(committed["end"])
active_prime = committed["active_prime"]
range_size = range_end - range_start + 1

if active_prime is None:
    applied_primes: tuple[int, ...] = ()
else:
    active_index = FILTER_PRIMES.index(active_prime)
    applied_primes = FILTER_PRIMES[: active_index + 1]

values, survives, eliminated_by, confirmed, frontier = compute_sieve_state(
    range_start,
    range_end,
    applied_primes,
)

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

if frontier is None:
    proof_coverage_count = 0
else:
    proof_coverage_count = int(
        np.count_nonzero(candidate_mask & (values < frontier))
    )
proof_coverage = (
    proof_coverage_count / initial_candidates
    if initial_candidates
    else 0.0
)

state_token = experiment_token(range_start, range_end, active_prime)

st.caption(
    f"Active experiment: integers {range_start:,} through {range_end:,} · "
    + (
        "no prime filters applied"
        if active_prime is None
        else f"filters through Prime {active_prime}"
    )
)

metric_1, metric_2, metric_3, metric_4, metric_5 = st.columns(5)
metric_1.metric("Prime candidates", f"{initial_candidates:,}", border=True)
metric_2.metric("Resolved composites", f"{eliminated_count:,}", border=True)
metric_3.metric("Unresolved candidates", f"{unresolved_count:,}", border=True)
metric_4.metric("Confirmed primes", f"{confirmed_count:,}", border=True)
metric_5.metric("Proof coverage of range", f"{proof_coverage:.1%}", border=True)

if active_prime is None:
    st.info(
        "No divisibility filters are active. Every integer at least 2 remains unresolved, so no prime has yet been certified by this experiment."
    )
elif frontier is not None and frontier > range_end:
    st.success(
        f"Complete certification coverage: every surviving candidate in the selected range is proven prime. The current proof frontier is n < {frontier:,}."
    )
else:
    coverage_end = min(range_end, frontier - 1) if frontier is not None else None
    st.info(
        f"Prime {active_prime} uniquely resolves {newly_eliminated:,} candidates that survived every earlier filter. "
        + (
            f"Survivors through {coverage_end:,} are confirmed prime; survivors above that boundary remain unresolved."
            if coverage_end is not None and coverage_end >= range_start
            else "The current proof frontier lies before the selected visible range."
        )
    )


visual_tab, analysis_tab, data_tab = st.tabs(
    [
        "Visual field",
        "Filter analysis",
        "Exact data",
    ]
)

with visual_tab:
    st.subheader("2. Inspect the same state under different projections")
    st.caption(
        "Changing projection changes geometry only. If an apparent pattern disappears under a nearby projection, it may be a display artifact rather than arithmetic structure."
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
            key=f"prime_lab_projection_{state_token}",
            help="Every option displays the same committed sieve state.",
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
                    key=f"prime_lab_custom_width_{state_token}",
                    help="Try nearby widths to test whether an alignment depends on row geometry.",
                )
            )
        elif projection == ACTIVE_PRIME_VIEW:
            projection_grid_width = int(active_prime)
            st.metric("Integers per row", f"{projection_grid_width:,}", border=True)
        else:
            st.metric("Remainder classes", "30", border=True)

    if projection == SQUARE_VIEW:
        st.write(
            f"Consecutive integers are wrapped into rows of {square_width:,}. This is a compact overview, but the row width can create geometric alignments."
        )
    elif projection == CUSTOM_WIDTH_VIEW:
        st.write(
            f"Exactly {projection_grid_width:,} integers are placed in each row. Changing only this width is a direct control for projection dependent patterns."
        )
    elif projection == ACTIVE_PRIME_VIEW:
        st.write(
            f"Rows contain {active_prime} integers. Equal remainders modulo {active_prime} align vertically, exposing the periodic structure of the selected filter."
        )
    else:
        st.write(
            "Integers are placed into 30 residue lanes. After filters 2, 3, and 5, every prime greater than 5 must occupy one of eight lanes: 1, 7, 11, 13, 17, 19, 23, or 29."
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
        chart_kind = "mod30"
    else:
        projection_figure = build_candidate_figure(
            values,
            survives,
            eliminated_by,
            active_prime,
            confirmed,
            grid_width=projection_grid_width,
        )
        chart_kind = "field"

    projection_width_token = projection_grid_width if projection_grid_width is not None else "auto"
    chart_key = (
        f"prime_lab_chart_{state_token}_{chart_kind}_"
        f"{projection.replace(' ', '_')}_{projection_width_token}"
    )
    projection_figure.update_layout(uirevision=chart_key)

    st.plotly_chart(
        projection_figure,
        width="stretch",
        config={
            "displaylogo": False,
            "responsive": True,
        },
        key=chart_key,
    )

    if range_size <= 400 and projection != MODULO_30_VIEW:
        st.caption(
            "Integer labels are drawn directly in fields of 400 values or fewer. Hover remains available for the exact state description."
        )
    elif projection != MODULO_30_VIEW:
        st.caption(
            "Direct labels are suppressed in dense fields. Hover over a cell to inspect its integer and exact state."
        )

    st.markdown("#### Inspect one integer")
    st.caption(
        "Use the inspector to translate a visual cell back into the exact sieve statement that produced it."
    )

    default_inspection = min(
        range_end,
        max(range_start, 53 if range_start <= 53 <= range_end else range_start),
    )

    with st.form(f"prime_lab_inspector_{state_token}", border=False):
        inspector_left, inspector_right = st.columns([1, 3])
        with inspector_left:
            inspected_value = int(
                st.number_input(
                    "Integer to inspect",
                    min_value=range_start,
                    max_value=range_end,
                    value=default_inspection,
                    step=1,
                )
            )
        with inspector_right:
            st.write("")
            st.write("")
            inspect_submit = st.form_submit_button("Inspect integer")

    inspected_index = inspected_value - range_start
    inspected_eliminator = int(eliminated_by[inspected_index])
    inspected_state = state_label(
        value=inspected_value,
        survives=bool(survives[inspected_index]),
        confirmed=bool(confirmed[inspected_index]),
        eliminated_by=inspected_eliminator,
    )

    inspect_one, inspect_two, inspect_three = st.columns(3)
    inspect_one.metric("Integer", f"{inspected_value:,}", border=True)
    inspect_two.metric("State", inspected_state, border=True)
    inspect_three.metric(
        "First eliminating prime",
        "None" if inspected_eliminator == 0 else str(inspected_eliminator),
        border=True,
    )

    if inspected_value < 2:
        st.caption("This integer is below 2 and is not a prime candidate.")
    elif confirmed[inspected_index]:
        st.caption(
            f"{inspected_value:,} survived every applied filter and lies below the proof frontier n < {frontier:,}, so the current experiment proves it prime."
        )
    elif survives[inspected_index]:
        st.caption(
            f"{inspected_value:,} survived the applied filters, but the current proof depth does not yet test every possible prime divisor through √{inspected_value:,}. It remains unresolved rather than being assumed prime."
        )
    else:
        st.caption(
            f"Prime {inspected_eliminator} is the first applied filter that divides {inspected_value:,}. Because filters are applied in ascending order, it is the smallest applied prime divisor that resolves this candidate as composite."
        )

    if projection == MODULO_30_VIEW:
        summaries = residue_class_summaries(
            values,
            survives,
            eliminated_by,
            confirmed,
            active_prime,
            modulus=30,
        )
        eligible_summaries = tuple(
            summary for summary in summaries if summary.prime_eligible
        )
        confirmed_above_five = int(
            np.count_nonzero(confirmed & (values > 5))
        )

        if confirmed_above_five:
            busiest_summary = max(
                eligible_summaries,
                key=lambda summary: (summary.confirmed, -summary.residue),
            )
            confirmed_counts = [
                summary.confirmed for summary in eligible_summaries
            ]
            busiest_label = (
                f"Lane {busiest_summary.residue} · "
                f"{busiest_summary.confirmed:,}"
            )
            spread_label = (
                f"{min(confirmed_counts):,} to {max(confirmed_counts):,}"
            )
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
            st.dataframe(
                pd.DataFrame(residue_rows),
                width="stretch",
                hide_index=True,
            )
            st.caption(
                "These counts describe only the selected finite range. A larger count in one residue lane is not evidence that the lane is permanently favored."
            )


with analysis_tab:
    st.subheader("3. Measure what each prime filter contributes")
    st.caption(
        "A prime receives credit only for candidates that survived every earlier filter and are first resolved by that prime."
    )

    if not applied_primes:
        st.info("Apply at least Prime 2 to measure filter contribution.")
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

        efficiency_metric_1, efficiency_metric_2, efficiency_metric_3, efficiency_metric_4 = st.columns(4)
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
            "Candidates after final filter",
            f"{current_efficiency.candidates_after:,}",
            border=True,
        )
        efficiency_metric_4.metric(
            "Largest unique contribution",
            f"Prime {strongest_step.prime} · {strongest_step.removed:,}",
            border=True,
        )

        efficiency_figure = build_filter_efficiency_figure(
            range_start,
            range_end,
            applied_primes,
        )
        efficiency_key = f"prime_lab_efficiency_{state_token}"
        efficiency_figure.update_layout(uirevision=efficiency_key)
        st.plotly_chart(
            efficiency_figure,
            width="stretch",
            config={"displaylogo": False, "responsive": True},
            key=efficiency_key,
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
        efficiency_frame = pd.DataFrame(efficiency_rows)

        table_col, export_col = st.columns([4, 1])
        with table_col:
            with st.expander("Exact filter contribution table", expanded=False):
                st.dataframe(
                    efficiency_frame,
                    width="stretch",
                    hide_index=True,
                    column_config={
                        "Marginal removal rate": st.column_config.NumberColumn(format="%.6f"),
                        "Cumulative survival rate": st.column_config.NumberColumn(format="%.6f"),
                    },
                )
        with export_col:
            st.download_button(
                "Download filter CSV",
                data=efficiency_frame.to_csv(index=False).encode("utf-8"),
                file_name=f"prime_lab_filters_{range_start}_{range_end}_{active_prime}.csv",
                mime="text/csv",
                width="stretch",
            )

        st.markdown("#### Interpretation")
        st.write(
            "Early prime filters usually remove a large share of candidates because their multiples are frequent. Later filters act on a population already stripped of smaller prime factors. The marginal removal rate therefore measures new information contributed at that stage, not the total number of multiples of the prime."
        )


with data_tab:
    st.subheader("4. Inspect and export the exact state")
    st.caption(
        "The table is the nonvisual form of the experiment. It provides a reproducible record for checking cells, comparing ranges, or continuing analysis outside Prime Lab."
    )

    state_rows = []
    for index, value in enumerate(values):
        first_eliminating_prime = (
            int(eliminated_by[index])
            if eliminated_by[index] > 0
            else None
        )
        state_rows.append(
            {
                "Integer": int(value),
                "State": state_label(
                    value=int(value),
                    survives=bool(survives[index]),
                    confirmed=bool(confirmed[index]),
                    eliminated_by=int(eliminated_by[index]),
                ),
                "First eliminating prime": first_eliminating_prime,
                "First eliminated by selected filter": bool(
                    active_prime is not None
                    and first_eliminating_prime == active_prime
                ),
                "Below proof frontier": bool(
                    frontier is not None
                    and value >= 2
                    and value < frontier
                ),
            }
        )

    state_frame = pd.DataFrame(state_rows)
    st.dataframe(
        state_frame,
        width="stretch",
        hide_index=True,
    )

    export_one, export_two, export_space = st.columns([1, 1, 3])
    with export_one:
        st.download_button(
            "Download state CSV",
            data=state_frame.to_csv(index=False).encode("utf-8"),
            file_name=f"prime_lab_state_{range_start}_{range_end}.csv",
            mime="text/csv",
            width="stretch",
        )
    with export_two:
        metadata_frame = pd.DataFrame(
            [
                {
                    "Range start": range_start,
                    "Range end": range_end,
                    "Final prime filter": active_prime,
                    "Applied prime sequence": ",".join(str(prime) for prime in applied_primes),
                    "Proof frontier exclusive": frontier,
                    "Prime candidates": initial_candidates,
                    "Resolved composites": eliminated_count,
                    "Unresolved candidates": unresolved_count,
                    "Confirmed primes": confirmed_count,
                }
            ]
        )
        st.download_button(
            "Download metadata CSV",
            data=metadata_frame.to_csv(index=False).encode("utf-8"),
            file_name=f"prime_lab_metadata_{range_start}_{range_end}.csv",
            mime="text/csv",
            width="stretch",
        )

    with st.expander("Methods, limits, and suggested controls", expanded=False):
        st.markdown(
            f"""
**Certification rule.** If every prime through p has been applied and q is the next prime after p, every surviving candidate below q² is confirmed prime.

**Finite display.** The baseline field is limited to {MAX_VISIBLE_INTEGERS:,} visible integers. This is a visualization limit, not a limit of prime arithmetic.

**Committed controls.** Range and filter changes are submitted together so an incomplete edit cannot leave the visualization in a transient state.

**Static by design.** Prime Lab displays an exact selected state without playback. Kinetic Sieve Lab is the dedicated real time view of divisibility events.

**Projection control.** Square and custom width grids can create apparent alignments. Compare nearby widths before treating a geometric pattern as arithmetic structure.

**Useful experiment.** Apply filters through Prime 5, inspect the modulo 30 projection, then deepen the filter one prime at a time. The eight prime eligible lanes remain fixed while additional composite positions are progressively resolved.

**Interpretation.** A visible pattern is an observation. Any proposed relationship should be measured, compared against known modular structure, and reproduced on independent ranges before it is treated as evidence.
            """
        )
