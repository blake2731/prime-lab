from math import isqrt

import pandas as pd
import streamlit as st

from prime_lab.prime_phase import (
    is_prime_from_relevant_phases,
    joint_phase_cycle,
    phase_state,
    phase_states,
    primes_up_to,
    relevant_divisor_primes,
    synchronized_primes,
)
from ui.prime_phase import (
    build_joint_phase_figure,
    build_phase_trace_figure,
    build_prime_clock_figure,
)


st.set_page_config(
    page_title="Prime Phase Space",
    page_icon="◉",
    layout="wide",
)

st.title("Prime Phase Space")
st.caption(
    "View divisibility as synchronized circular phase: every prime defines a repeating clock, and multiples occur when that clock returns to phase zero."
)

st.info(
    "For a prime p and integer n, Prime Lab normalizes the remainder n mod p into one turn of a circle. "
    "The phase is (n mod p) / p and the corresponding angle is 2π(n mod p) / p. "
    "A return to phase zero means p divides n exactly."
)

with st.expander("Why this connects to primality", expanded=True):
    st.write(
        "As n advances by one, every prime clock advances by one residue step. A composite integer is reached when at least one relevant earlier prime clock returns to phase zero. "
        "To prove that n is prime, it is enough to check prime cycles through √n. If none of those relevant clocks is at zero, n has no possible smaller prime divisor and is therefore prime."
    )
    st.write(
        "The clock for n itself is not used as evidence that n is composite. For example, the Prime 5 clock is at phase zero at n = 5, but 5 is still prime because no smaller relevant prime cycle divides it."
    )
    st.write(
        "When several prime clocks return to zero together, Prime Phase Space shows the same shared-multiple event that Kinetic Sieve Lab shows as trajectories meeting on the number line."
    )

st.subheader("1. Inspect one integer moment")
control_left, control_right = st.columns([1, 1])

with control_left:
    current_integer = int(
        st.number_input(
            "Integer n",
            min_value=2,
            max_value=100_000,
            value=30,
            step=1,
            help="Move through integer moments and watch every selected prime cycle change phase.",
        )
    )

with control_right:
    clock_count = int(
        st.slider(
            "Prime clocks to display",
            min_value=3,
            max_value=12,
            value=8,
            help="This changes only the displayed clocks. Primality classification still checks every prime through √n.",
        )
    )

available_primes = primes_up_to(37)
selected_primes = available_primes[:clock_count]
states = phase_states(current_integer, selected_primes)
selected_sync = synchronized_primes(current_integer, selected_primes)
relevant_zeros = relevant_divisor_primes(current_integer)
prime_now = is_prime_from_relevant_phases(current_integer)

metric_one, metric_two, metric_three, metric_four = st.columns(4)
metric_one.metric("Current integer", f"{current_integer:,}")
metric_two.metric("Classification", "Confirmed prime" if prime_now else "Composite")
metric_three.metric(
    "Relevant phase-zero clocks",
    "None" if not relevant_zeros else " · ".join(str(prime) for prime in relevant_zeros),
)
metric_four.metric("Proof only needs primes through", f"√n = {isqrt(current_integer)}")

if prime_now:
    st.success(
        f"{current_integer:,} is prime: none of the prime cycles through √{current_integer:,} returns to phase zero at this integer."
    )
else:
    st.warning(
        f"{current_integer:,} is composite: the relevant phase-zero prime cycle"
        f"{'s are' if len(relevant_zeros) != 1 else ' is'} "
        + ", ".join(str(prime) for prime in relevant_zeros)
        + "."
    )

st.plotly_chart(build_prime_clock_figure(states), width="stretch")

phase_rows = []
for state in states:
    phase_rows.append(
        {
            "Prime cycle": state.prime,
            "n mod p": state.remainder,
            "Normalized phase": round(state.phase_fraction, 4),
            "Angle": f"{state.angle_degrees:.1f}°",
            "At phase zero": "Yes" if state.is_zero_crossing else "No",
            "Relevant divisor test": "Yes" if state.is_relevant_divisor else "No",
        }
    )

with st.expander("Exact phase values", expanded=False):
    st.dataframe(pd.DataFrame(phase_rows), width="stretch", hide_index=True)
    st.code(
        "Phase signature: ("
        + ", ".join(f"{state.prime}:{state.remainder}" for state in states)
        + ")",
        language=None,
    )

if selected_sync:
    st.caption(
        "Selected clocks currently at phase zero: "
        + ", ".join(str(prime) for prime in selected_sync)
        + ". A phase-zero clock is a divisor only when the prime is smaller than the current integer."
    )

st.subheader("2. Project two prime cycles into phase space")
st.write(
    "A pair of prime clocks can be represented as one point in a square. The horizontal coordinate is the phase of one prime cycle and the vertical coordinate is the phase of the other. "
    "As n advances, the point visits a sequence of joint states before repeating."
)

pair_left, pair_right = st.columns(2)
pair_options = list(selected_primes)
with pair_left:
    first_prime = int(
        st.selectbox(
            "Horizontal prime cycle",
            pair_options,
            index=min(1, len(pair_options) - 1),
        )
    )
with pair_right:
    second_options = [prime for prime in pair_options if prime != first_prime]
    second_prime = int(
        st.selectbox(
            "Vertical prime cycle",
            second_options,
            index=min(1, len(second_options) - 1),
        )
    )

joint_points = joint_phase_cycle(first_prime, second_prime)
joint_period = first_prime * second_prime
st.caption(
    f"Because {first_prime} and {second_prime} are distinct primes, their joint phase state repeats every {joint_period} integers. "
    "The shared zero state is their common-multiple synchronization point."
)
st.plotly_chart(
    build_joint_phase_figure(
        joint_points,
        first_prime=first_prime,
        second_prime=second_prime,
        current_integer=current_integer,
    ),
    width="stretch",
)

st.subheader("3. Watch the phase rhythms around this integer")
trace_radius = int(
    st.slider(
        "Integers on each side",
        min_value=10,
        max_value=80,
        value=30,
        step=5,
    )
)
trace_start = max(0, current_integer - trace_radius)
trace_stop = current_integer + trace_radius
trace_integers = tuple(range(trace_start, trace_stop + 1))
trace_primes = selected_primes[: min(5, len(selected_primes))]
states_by_prime = {
    prime: tuple(phase_state(integer, prime) for integer in trace_integers)
    for prime in trace_primes
}
st.plotly_chart(
    build_phase_trace_figure(trace_integers, states_by_prime),
    width="stretch",
)
st.caption(
    "Every trace is a normalized modular sawtooth. A return to phase 0 is an exact multiple of that prime. "
    "When several traces reach zero at the same integer, the corresponding prime cycles synchronize."
)

with st.expander("Questions to experiment with", expanded=False):
    st.markdown(
        """
1. Compare a prime integer with the composites immediately before and after it. Which relevant clocks are closest to phase zero?
2. Move to 30, 60, 90, and 210. How do multi-prime synchronization events appear in the clocks and in the two-cycle projection?
3. Compare different pairs of prime cycles. How does the joint repetition period change?
4. Look at prime gaps as intervals where at least one relevant prime cycle reaches zero at every intermediate integer.
5. Record phase signatures around primes and ask whether any apparent similarity survives comparison with ordinary sieve structure.
        """
    )

st.warning(
    "Prime Phase Space is a different coordinate system for exact modular arithmetic, not evidence that circles or π cause prime numbers. "
    "The purpose is to expose periodic structure in a form that can be measured and compared."
)
