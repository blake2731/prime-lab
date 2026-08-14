from math import exp

import pandas as pd
import streamlit as st

from prime_lab.primorial_phase import (
    EULER_MASCHERONI,
    density_convergence_sweep,
    prime_density_observation,
    primorial_stages,
    survivor_residues,
)
from ui.primorial_phase import (
    build_asymptotic_residual_figure,
    build_density_comparison_figure,
    build_density_residual_figure,
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
    "Measure how progressively activated prime cycles reduce the joint modular state space that avoids phase zero."
)

st.info(
    "For active prime cycles p₁, p₂, ..., pₖ, the complete joint residue state repeats after the primorial P = p₁p₂...pₖ. "
    "A state survives when none of the active cycles is at phase zero. Exactly ∏(p − 1) states survive, giving the survivor fraction ∏(1 − 1/p)."
)

with st.expander("Relationship to other Prime Lab views", expanded=True):
    st.write(
        "Kinetic Sieve Lab represents divisibility as repeated landings on the number line. Prime Phase Space represents the same modular cycles as circular phase coordinates. "
        "Primorial Phase Space combines several prime cycles and measures the portion of their joint residue space that remains eligible after phase zero states are excluded."
    )
    st.write(
        "For the active primes 2, 3, and 5, the joint cycle has length 30. Exactly eight residues avoid phase zero on all three cycles: 1, 7, 11, 13, 17, 19, 23, and 29. "
        "These are the same modulo 30 prime eligible residue classes shown elsewhere in Prime Lab."
    )
    st.caption(
        "A surviving residue class is eligible relative to the active prime cycles; it is not automatically prime. Larger prime factors can still resolve integers in that class as composite."
    )


st.subheader("1. Primorial sieve staircase")
st.write(
    "Each stage activates one additional prime cycle. The primorial P counts every possible joint residue state in one complete period. "
    "Euler's totient φ(P) counts exactly those states that avoid phase zero on every active cycle."
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
        "New prime cycle": stage.prime,
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
    "It approximates the exact primorial survivor product as the prime cutoff grows. It is a classical asymptotic result, not a fitted Prime Lab formula."
)


st.subheader("2. Primorial survivor wheel")
st.write(
    "One complete primorial residue period can be wrapped around a circle. Blue points avoid phase zero on every active prime cycle. "
    "Gray points reach phase zero on at least one active cycle and are excluded by that primorial filter."
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
        + ". This is the modulo 30 prime eligible residue set in circular phase form."
    )
else:
    st.caption(
        "The blue positions are prime eligible residue classes relative to the active cycles. They are not all prime numbers. "
        "Additional prime cycles can still eliminate integers occupying these residue classes."
    )


st.subheader("3. Periodic survivor density and observed prime density")
st.write(
    "This comparison places distinct quantities beside one another. The primorial survivor fraction is a periodic residue density. "
    "π(x) / x is the finite observed fraction of integers through x that are prime, while 1 / ln(x) is the leading Prime Number Theorem density approximation. "
    "The quantities are related, but they should not be interpreted as interchangeable probabilities."
)

observation_integer = int(
    st.number_input(
        "Observe primes through x",
        min_value=100,
        max_value=MAX_DENSITY_INTEGER,
        value=1_000_000,
        step=100,
        help="The exact interactive count is capped at ten million so π(x) can be recomputed without a large persistent memory cost.",
    )
)

with st.spinner("Counting primes and building the √x primorial comparison..."):
    observation = prime_density_observation(observation_integer)

obs_one, obs_two, obs_three, obs_four = st.columns(4)
obs_one.metric("π(x)", f"{observation.prime_count:,}")
obs_two.metric("Observed π(x) / x", f"{observation.empirical_prime_density:.6f}")
obs_three.metric("PNT 1 / ln(x)", f"{observation.pnt_density:.6f}")
obs_four.metric(
    "√x proof cycles",
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
    "With the prime cutoff chosen near √x, Mertens' product is approximately e^(−γ) / ln(√x) = 2e^(−γ) / ln(x). "
    "Therefore the primorial survivor fraction is not expected to collapse directly onto 1 / ln(x). "
    f"The classical comparison constant 2e^(−γ) is approximately {2 * exp(-EULER_MASCHERONI):.6f}."
)


st.subheader("4. Error and convergence across scale")
st.write(
    "Single values can look close by coincidence or by an established asymptotic relationship. A convergence sweep measures the signed discrepancies at the same checkpoints instead. "
    "The experiment below evaluates powers of ten with one exact Eratosthenes sieve and compares four residual quantities."
)

with st.expander("How to interpret the residuals", expanded=True):
    st.markdown(
        """
**Prime density minus PNT density** measures `π(x)/x − 1/ln(x)`. A positive value means the observed finite prime density is above the leading PNT density approximation at that x.

**Primorial survivor minus prime density** measures how much periodic phase space survives the √x prime cycles beyond the fraction of integers that are actually prime. A positive value means the primorial filter leaves more candidates than there are primes.

**Survivor/PNT ratio minus 2e^(−γ)** measures convergence toward the classical √x cutoff comparison. Zero would mean the finite ratio equals that asymptotic reference exactly.

**Exact survivor minus Mertens estimate** measures the finite error in using `e^(−γ)/ln(p)` for the primorial survivor product at the proof cutoff prime p. Zero would mean exact agreement at that cutoff.
        """
    )

sweep_exponent = int(
    st.select_slider(
        "Sweep through",
        options=[4, 5, 6, 7],
        value=7,
        format_func=lambda exponent: f"10^{exponent}",
        help="The sweep begins at 10² and uses one exact prime sieve through the selected maximum power of ten.",
    )
)

with st.spinner("Computing exact convergence checkpoints..."):
    convergence = density_convergence_sweep(2, sweep_exponent)

latest_convergence = convergence[-1]
conv_one, conv_two, conv_three, conv_four = st.columns(4)
conv_one.metric(
    "π(x)/x − 1/ln(x)",
    f"{latest_convergence.prime_density_minus_pnt:+.8f}",
)
conv_two.metric(
    "Survivor − π(x)/x",
    f"{latest_convergence.wheel_minus_prime_density:+.8f}",
)
conv_three.metric(
    "Ratio residual",
    f"{latest_convergence.wheel_ratio_error:+.8f}",
)
conv_four.metric(
    "Mertens residual",
    f"{latest_convergence.mertens_absolute_error:+.8f}",
)

st.plotly_chart(build_density_residual_figure(convergence), width="stretch")
st.caption(
    "The zero line is the reference. Crossing it indicates a change in the sign of the finite discrepancy; a sign change by itself does not imply a new theorem or a persistent oscillation."
)

st.plotly_chart(build_asymptotic_residual_figure(convergence), width="stretch")
st.caption(
    "The two residuals in this chart compare different mathematical objects, so their vertical proximity should not be interpreted as equality. "
    "The useful information is how each residual behaves as x increases."
)

convergence_rows = [
    {
        "x": point.maximum_integer,
        "π(x)": point.prime_count,
        "π(x) / x": point.empirical_prime_density,
        "1 / ln(x)": point.pnt_density,
        "Primorial survivor": point.wheel_survivor_fraction,
        "π(x)/x − PNT": point.prime_density_minus_pnt,
        "Survivor − π(x)/x": point.wheel_minus_prime_density,
        "Survivor / PNT": point.wheel_to_pnt_ratio,
        "Ratio − 2e^(−γ)": point.wheel_ratio_error,
        "Exact − Mertens": point.mertens_absolute_error,
        "Relative Mertens error": point.mertens_relative_error,
        "√x cutoff prime": point.proof_cutoff_prime,
    }
    for point in convergence
]

with st.expander("Exact convergence table", expanded=False):
    st.dataframe(
        pd.DataFrame(convergence_rows),
        width="stretch",
        hide_index=True,
        column_config={
            "π(x) / x": st.column_config.NumberColumn(format="%.9f"),
            "1 / ln(x)": st.column_config.NumberColumn(format="%.9f"),
            "Primorial survivor": st.column_config.NumberColumn(format="%.9f"),
            "π(x)/x − PNT": st.column_config.NumberColumn(format="%+.9f"),
            "Survivor − π(x)/x": st.column_config.NumberColumn(format="%+.9f"),
            "Survivor / PNT": st.column_config.NumberColumn(format="%.9f"),
            "Ratio − 2e^(−γ)": st.column_config.NumberColumn(format="%+.9f"),
            "Exact − Mertens": st.column_config.NumberColumn(format="%+.9f"),
            "Relative Mertens error": st.column_config.NumberColumn(format="%+.6f"),
        },
    )


st.subheader("5. Research directions")
st.markdown(
    """
1. Extend the convergence sweep and determine which residuals decrease monotonically, change sign, or require a different normalization.
2. Compare local prime density within individual surviving residue classes rather than treating all primorial survivors as equivalent.
3. Measure the spacing distribution between consecutive surviving residues for modulo 30, 210, 2310, and 30030 wheels.
4. Compare finite sieve residuals with established analytic number theory bounds before assigning significance to apparent structure.
5. Export reproducible datasets for any pattern that persists across independent ranges and parameter choices.
    """
)

st.warning(
    "Primorial Phase Space reorganizes established modular arithmetic, Euler totients, Mertens' product, and prime counting into an experimental coordinate system. "
    "Visual alignment, numerical proximity, or a residual trend is not evidence of a new theorem by itself. Any candidate pattern should be tested against established theory and independent numerical ranges."
)
