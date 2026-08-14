from math import exp

import pandas as pd
import streamlit as st

from prime_lab.primorial_phase import (
    EULER_MASCHERONI,
    prime_density_observation,
    primorial_stages,
    survivor_residues,
)
from ui.primorial_phase import (
    build_density_comparison_figure,
    build_primorial_wheel_figure,
    build_survivor_fraction_figure,
)


MAX_STAGES = 15
MAX_WHEEL_STAGE = 6
MAX_DENSITY_INTEGER = 10_000_000


st.set_page_config(
    page_title="Primorial Phase Space",
    page_icon="⊙",
    layout="wide",
)

st.title("Primorial Phase Space")
st.caption(
    "Activate prime cycles one at a time and measure how much joint modular phase space still avoids phase zero."
)

st.info(
    "If the active prime clocks are p₁, p₂, ..., pₖ, their joint residue state repeats after the primorial P = p₁p₂...pₖ. "
    "A state survives when none of those clocks is at phase zero. Exactly ∏(p − 1) states survive, so the surviving fraction is ∏(1 − 1/p)."
)

with st.expander("Why this connects the earlier Prime Lab experiments", expanded=True):
    st.write(
        "Kinetic Sieve Lab shows prime cycles arriving on the number line. Prime Phase Space turns those cycles into circular phase coordinates. "
        "Primorial Phase Space now asks how much of the combined phase space remains after each new prime cycle excludes its phase-zero slice."
    )
    st.write(
        "At the 2, 3, and 5 stage, the joint cycle has length 30 and exactly eight residues avoid phase zero on all three clocks: 1, 7, 11, 13, 17, 19, 23, and 29. "
        "That is the same modulo 30 candidate structure already visible elsewhere in Prime Lab, expressed as a primorial phase survivor set."
    )


st.subheader("1. Build the primorial sieve staircase")
st.write(
    "Each stage activates one additional prime clock. The primorial counts all possible joint residue states in one complete cycle; Euler's totient of that primorial counts the states that avoid phase zero on every active clock."
)

stage_count = int(
    st.slider(
        "Prime cycles to activate",
        min_value=3,
        max_value=MAX_STAGES,
        value=10,
        help="The arithmetic remains exact. Large primorials are handled as integers without enumerating every joint state.",
    )
)

stages = primorial_stages(stage_count)
latest = stages[-1]

metric_one, metric_two, metric_three, metric_four = st.columns(4)
metric_one.metric("Largest active prime", f"{latest.prime}")
metric_two.metric("Primorial joint states", f"{latest.primorial:,}")
metric_three.metric("Surviving states", f"{latest.surviving_states:,}")
metric_four.metric("Survivor fraction", f"{latest.survivor_fraction:.6f}")

st.plotly_chart(build_survivor_fraction_figure(stages), width="stretch")

stage_rows = [
    {
        "Stage": stage.stage,
        "New prime clock": stage.prime,
        "Primorial P": stage.primorial,
        "Surviving states φ(P)": stage.surviving_states,
        "Survivor fraction": stage.survivor_fraction,
        "Eliminated fraction": stage.eliminated_fraction,
        "Mertens estimate": stage.mertens_estimate,
        "Exact / Mertens": stage.survivor_to_mertens_ratio,
    }
    for stage in stages
]

with st.expander("Exact stage table", expanded=False):
    st.dataframe(
        pd.DataFrame(stage_rows),
        width="stretch",
        hide_index=True,
        column_config={
            "Survivor fraction": st.column_config.NumberColumn(format="%.8f"),
            "Eliminated fraction": st.column_config.NumberColumn(format="%.8f"),
            "Mertens estimate": st.column_config.NumberColumn(format="%.8f"),
            "Exact / Mertens": st.column_config.NumberColumn(format="%.6f"),
        },
    )

st.caption(
    "The dashed curve is the classical Mertens approximation e^(−γ) / ln(p), where γ is the Euler Mascheroni constant. "
    "It approximates the primorial survivor product as the prime cutoff grows; it is not a fitted Prime Lab formula."
)


st.subheader("2. See one complete primorial survivor wheel")
st.write(
    "Now take one full primorial residue period and wrap it around a circle. Blue points are residue states that avoid phase zero on every active prime clock. Gray points touch phase zero on at least one clock and are therefore excluded by that primorial filter."
)

wheel_stage = int(
    st.slider(
        "Wheel stage",
        min_value=1,
        max_value=min(MAX_WHEEL_STAGE, stage_count),
        value=min(3, stage_count),
        help="The wheel is capped at the first six prime cycles so every residue in the period can still be rendered directly.",
    )
)
wheel_primes = tuple(stage.prime for stage in stages[:wheel_stage])
wheel_modulus, wheel_survivors = survivor_residues(wheel_primes)
wheel_cutoff = wheel_primes[-1]

wheel_one, wheel_two, wheel_three = st.columns(3)
wheel_one.metric("Primorial period", f"{wheel_modulus:,}")
wheel_two.metric("Surviving residues", f"{len(wheel_survivors):,}")
wheel_three.metric("Survivor fraction", f"{len(wheel_survivors) / wheel_modulus:.6f}")

st.plotly_chart(
    build_primorial_wheel_figure(
        modulus=wheel_modulus,
        survivor_residues=wheel_survivors,
        cutoff_prime=wheel_cutoff,
    ),
    width="stretch",
)

if wheel_modulus == 30:
    st.success(
        "At P = 30 the surviving residues are exactly: "
        + ", ".join(str(residue) for residue in wheel_survivors)
        + ". This is Prime Lab's modulo 30 candidate set in circular phase form."
    )
else:
    st.caption(
        "These blue positions are prime eligible residue classes relative to the active clocks. They are not all prime numbers. "
        "Larger prime cycles can still eliminate numbers occupying these residue classes."
    )


st.subheader("3. Compare periodic survivor density with actual prime density")
st.write(
    "This comparison deliberately places two different quantities beside one another. The primorial survivor fraction is a periodic residue density. π(x) / x is the observed fraction of integers up to x that are prime. "
    "Their difference is part of what a sieve analysis must understand rather than something to hide."
)

observation_integer = int(
    st.number_input(
        "Observe primes through x",
        min_value=100,
        max_value=MAX_DENSITY_INTEGER,
        value=1_000_000,
        step=100,
        help="V1 caps this exact counting comparison at ten million so Streamlit can recompute π(x) interactively without a large persistent memory cost.",
    )
)

with st.spinner("Counting primes and building the √x primorial comparison..."):
    observation = prime_density_observation(observation_integer)

obs_one, obs_two, obs_three, obs_four = st.columns(4)
obs_one.metric("π(x)", f"{observation.prime_count:,}")
obs_two.metric("Observed π(x) / x", f"{observation.empirical_prime_density:.6f}")
obs_three.metric("PNT 1 / ln(x)", f"{observation.pnt_density:.6f}")
obs_four.metric(
    "√x proof clocks",
    f"{observation.proof_prime_count:,} through {observation.proof_cutoff_prime:,}",
)

st.plotly_chart(build_density_comparison_figure(observation), width="stretch")

ratio_left, ratio_right = st.columns(2)
ratio_left.metric(
    "Primorial survivor / PNT density",
    f"{observation.wheel_to_pnt_ratio:.6f}",
)
ratio_right.metric(
    "Asymptotic √x comparison constant 2e^(−γ)",
    f"{observation.expected_sqrt_ratio:.6f}",
)

st.info(
    "Why the blue primorial bar does not simply collapse onto 1 / ln(x): when the prime cutoff is chosen near √x, Mertens' product is approximately "
    "e^(−γ) / ln(√x) = 2e^(−γ) / ln(x). The factor 2e^(−γ) is about "
    f"{2 * exp(-EULER_MASCHERONI):.6f}. This is classical sieve behavior, not a newly discovered discrepancy."
)


st.subheader("4. What is worth investigating from here")
st.markdown(
    """
1. Track how the exact survivor product approaches the Mertens approximation as more prime clocks are activated.
2. Compare the periodic survivor fraction with π(x) / x over increasing x and measure their ratio rather than judging the curves visually.
3. Study how the modulo 30 survivor set grows into modulo 210, 2310, and 30030 wheels while preserving exact phase-zero exclusion rules.
4. Compare local prime density inside specific surviving residue classes instead of treating every surviving state as equally likely to contain a prime.
5. Connect the remaining discrepancy to established sieve theory before treating any residual pattern as potentially new.
    """
)

st.warning(
    "Primorial Phase Space reorganizes established modular arithmetic, Euler totients, Mertens' product, and prime counting into one experimental view. "
    "A visual alignment or numerical ratio is not evidence of a new theorem by itself. The research value is in making exact comparisons easy enough to test systematically."
)
