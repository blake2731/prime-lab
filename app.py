import numpy as np
import streamlit as st

from prime_lab.certification import (
    certification_frontier,
    confirmed_prime_mask,
)
from prime_lab.filters import filter_candidates
from prime_lab.sonification import (
    PENTATONIC_NOTE_NAMES,
    PRIME_ELIGIBLE_RESIDUES,
    render_prime_gap_wav,
)
from ui.candidate_grid import build_candidate_figure
from ui.residue_animation import build_residue_animation
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


st.set_page_config(
    page_title="Prime Lab",
    page_icon="∴",
    layout="wide",
)


st.title("Prime Lab")

st.caption("Computational Number Theory Laboratory  •  Candidate Filter Visualizer")


with st.container(border=True):
    st.subheader("Experiment controls")

    col_start, col_end, col_filter = st.columns([1, 1, 1.25])

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
            value=500,
            step=1,
        )

    with col_filter:
        filter_options = [
            None,
            *FILTER_PRIMES,
        ]

        active_prime = st.selectbox(
            "Apply filters through",
            filter_options,
            index=0,
            format_func=lambda value: (
                "No filters" if value is None else f"Prime {value}"
            ),
        )


if range_end < range_start:
    st.error("Range end must be greater than or equal to range start.")
    st.stop()


range_size = range_end - range_start + 1


if range_size > 5000:
    st.warning("The first visual build is limited to 5,000 visible integers.")
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
    "Integers",
    f"{range_size:,}",
    border=True,
)

metric_2.metric(
    "Candidates remaining",
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
    "Candidate survival",
    f"{survival_rate:.2%}",
    border=True,
)


with st.container(border=True):
    st.subheader("Projection lab")

    square_width = max(
        10,
        int(np.ceil(np.sqrt(range_size))),
    )

    projection_options = [
        "Square fit",
        "Fixed width",
    ]

    if active_prime is not None:
        projection_options.append(
            "Active prime width"
        )

    projection_options.append(
        "Modulo 30"
    )

    projection_control, projection_detail = st.columns(
        [1, 2]
    )

    with projection_control:
        projection = st.selectbox(
            "Projection",
            projection_options,
            key="projection_mode",
        )

    projection_grid_width = None

    with projection_detail:
        if projection == "Square fit":
            st.metric(
                "Grid width",
                f"{square_width:,}",
                border=True,
            )

            projection_grid_width = None

        elif projection == "Fixed width":
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
                    "Grid width",
                    min_value=2,
                    max_value=maximum_width,
                    value=default_width,
                    step=1,
                    key="fixed_projection_width",
                )
            )

        elif projection == "Active prime width":
            projection_grid_width = int(
                active_prime
            )

            st.metric(
                "Grid width",
                f"{projection_grid_width:,}",
                border=True,
            )

        else:
            st.metric(
                "Wheel modulus",
                "30",
                border=True,
            )

    if projection == "Modulo 30":
        if applied_primes:
            projection_figure = build_residue_animation(
                range_start,
                range_end,
                applied_primes,
            )

        else:
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

    if projection == "Square fit":
        st.caption(
            f"Square fit wraps consecutive integers every {square_width:,} cells. "
            "It is useful for overall density, but some alignments can be created by the chosen width."
        )

    elif projection == "Fixed width":
        st.caption(
            f"Fixed width wraps consecutive integers every {projection_grid_width:,} cells. "
            "Change only the width to test whether a visible pattern survives a different projection."
        )

    elif projection == "Active prime width":
        st.caption(
            f"The field is wrapped every {active_prime} integers. "
            f"Values with the same remainder modulo {active_prime} align vertically, "
            "making the active filter geometry explicit."
        )

    elif active_prime is None or active_prime < 5:
        st.caption(
            "Apply filters through prime 5 to expose the full modulo 30 candidate corridors "
            "created by eliminating multiples of 2, 3, and 5."
        )

    else:
        st.caption(
            "Modulo 30 groups integers by residue class. "
            "After prime 5, only residues 1, 7, 11, 13, 17, 19, 23, and 29 "
            "remain prime eligible above 5."
        )

    if projection == "Modulo 30":
        with st.expander(
            "Listen to prime structure",
            expanded=False,
        ):
            st.write(
                "Pitch encodes modulo 30 residue using a stable C major pentatonic mapping. "
                "Rhythm comes from the exact gaps between consecutive confirmed primes. "
                "Music theory shapes the sound, while the prime data determines every note event."
            )

            sound_control, sound_detail = st.columns(
                [1, 2]
            )

            with sound_control:
                sonification_bpm = st.select_slider(
                    "Tempo",
                    options=[
                        180,
                        240,
                        300,
                        360,
                        420,
                        480,
                        600,
                    ],
                    value=360,
                    format_func=lambda value: f"{value} BPM",
                    key="prime_sonification_bpm",
                )

            with sound_detail:
                mapping_text = "   ".join(
                    f"{residue}→{note_name}"
                    for residue, note_name in zip(
                        PRIME_ELIGIBLE_RESIDUES,
                        PENTATONIC_NOTE_NAMES,
                    )
                )

                st.code(mapping_text)

                st.caption(
                    "For primes above 5, residue lane determines pitch. "
                    "The special primes 2, 3, and 5 use C3, G3, and C4 as opening anchor tones. "
                    "Stereo position follows residue order from low to high lanes."
                )

            if confirmed_count == 0:
                st.info(
                    "No primes are mathematically confirmed at this filter stage yet."
                )

            else:
                sonification_audio = render_prime_gap_wav(
                    values,
                    confirmed,
                    modulus=30,
                    bpm=int(sonification_bpm),
                )

                if sonification_audio:
                    st.audio(
                        sonification_audio,
                        format="audio/wav",
                    )

                    st.caption(
                        f"Sounding {confirmed_count:,} confirmed primes. "
                        "One integer of numerical distance maps to one sixteenth note unit before any global compression. "
                        "If a sequence would exceed 45 seconds, the full timeline is compressed uniformly, preserving every prime gap ratio."
                    )

with st.container(border=True):
    st.subheader("Current filter")

    if active_prime is None:
        st.write(
            "No divisibility filters have been applied. "
            "Every integer greater than 1 begins as a candidate."
        )

    else:
        detail_left, detail_right = st.columns([2, 1])

        with detail_left:
            st.write(
                f"Every prime filter through {active_prime} "
                "has now been applied."
            )

            st.code(f"n % {active_prime} == 0")

            if frontier is not None:
                st.caption(
                    f"Every surviving candidate below {frontier:,} "
                    "is now mathematically confirmed prime."
                )

            st.caption(
                "Gray marks resolved composites. "
                "Blue marks unresolved candidates. "
                "Teal marks confirmed primes. "
                "Amber marks the current elimination event."
            )

        with detail_right:
            st.metric(
                f"Removed by {active_prime}",
                f"{newly_eliminated:,}",
                border=True,
            )

            st.metric(
                "Confirmed primes",
                f"{confirmed_count:,}",
                border=True,
            )

    st.caption(
        "A surviving candidate becomes confirmed once every possible "
        "prime divisor up to its square root has been ruled out."
    )
