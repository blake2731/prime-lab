from math import isqrt

import pandas as pd
import streamlit as st

from prime_lab.prime_phase import (
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


MAX_INTEGER = 1_000_000_000_000


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
            max_value=MAX_INTEGER,
            value=30,
            step=1,
            help=(
                "Move through integer moments and watch selected prime cycles change phase. "
                "The current V1 ceiling is one trillion; it is a practical interface limit rather than a mathematical boundary."
            ),
        )
    )

with control_right:
    clock_count = int(
        st.slider(
            "Base prime clocks to display",
            min_value=3,
            max_value=12,
            value=8,
            help=(
                "Shows the first N prime cycles. Any additional phase-zero divisor clocks are added automatically so the visualization cannot hide the reason a number is composite."
            ),
        )
    )

proof_limit = isqrt(current_integer)
proof_primes = primes_up_to(proof_limit)
relevant_zeros = relevant_divisor_primes(current_integer)
prime_now = not relevant_zeros

available_primes = primes_up_to(37)
base_primes = available_primes[:clock_count]
extra_divisor_primes = tuple(prime for prime in relevant_zeros if prime not in base_primes)
display_primes = tuple(sorted(set(base_primes + extra_divisor_primes)))
states = phase_states(current_integer, display_primes)
selected_sync = synchronized_primes(current_integer, display_primes)

metric_one, metric_two, metric_three, metric_four = st.columns(4)
metric_one.metric("Current integer", f"{current_integer:,}")
metric_two.metric("Classification", "Confirmed prime" if prime_now else "Composite")
metric_three.metric(
    "Phase-zero divisor clocks",
    "None" if not relevant_zeros else " · ".join(str(prime) for prime in relevant_zeros),
)
metric_four.metric(
    "Prime cycles needed for proof",
    f"{len(proof_primes):,} through √n = {proof_limit:,}",
)

if prime_now:
    st.success(
        f"{current_integer:,} is prime: none of the {len(proof_primes):,} prime cycles through √{current_integer:,} returns to phase zero at this integer."
    )
else:
    st.warning(
        f"{current_integer:,} is composite because the prime cycle"
        f"{'s' if len(relevant_zeros) != 1 else ''} "
        + ", ".join(str(prime) for prime in relevant_zeros)
        + " return to phase zero here."
    )

if extra_divisor_primes:
    st.info(
        "The base clock selection would have hidden part of the explanation, so Prime Lab automatically added divisor clock"
        + ("s " if len(extra_divisor_primes) != 1 else " ")
        + ", ".join(str(prime) for prime in extra_divisor_primes)
        + "."
    )

st.caption(
    f"The clock panel visualizes {len(display_primes)} cycle{'s' if len(display_primes) != 1 else ''}. "
    f"The primality proof itself checks all {len(proof_primes):,} prime cycles through √n. "
    "A teal clock is part of the phase picture; amber emphasis is reserved for a clock that is actually at phase zero and divides n."
)

st.plotly_chart(build_prime_clock_figure(states), width="stretch")

phase_rows = []
for state in states:
    if state.is_relevant_divisor:
        role = "Phase-zero divisor"
        now = "ZERO"
    elif state.is_relevant_test_prime:
        role = "In √n proof"
        now = f"remainder {state.remainder}"
    else:
        role = "Displayed context"
        now = f"remainder {state.remainder}"

    phase_rows.append(
        {
            "Prime cycle": state.prime,
            "State now": now,
            "Next zero": state.next_zero,
            "Steps to next zero": state.steps_to_next_zero,
            "Normalized phase": round(state.phase_fraction, 4),
            "Angle": f"{state.angle_degrees:.1f}°",
            "Role": role,
        }
    )

with st.expander("Read the clocks as a schedule", expanded=True):
    st.write(
        "Each row says where one prime cycle is now and when it will next return to zero. "
        "This is the circular version of the landing schedule in Kinetic Sieve Lab."
    )
    st.dataframe(pd.DataFrame(phase_rows), width="stretch", hide_index=True)
    st.code(
        "Phase signature: ("
        + ", ".join(f"{state.prime}:{state.remainder}" for state in states)
        + ")",
        language=None,
    )

if selected_sync:
    st.caption(
        "Displayed clocks currently at phase zero: "
        + ", ".join(str(prime) for prime in selected_sync)
        + ". Prime Lab distinguishes these exact zero crossings from clocks that are merely part of the √n proof range."
    )

st.subheader("2. Project two prime cycles into phase space")
st.write(
    "A pair of prime clocks can be represented as one point in a square. The horizontal coordinate is the phase of one prime cycle and the vertical coordinate is the phase of the other. "
    "As n advances, the point visits a sequence of joint states before repeating."
)

pair_left, pair_right = st.columns(2)
pair_options = list(base_primes)
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
    "The shared zero state is their common-multiple synchronization point. The two-cycle projection is intentionally limited to the base clocks so its full repeating cycle stays lightweight."
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
trace_primes = display_primes[: min(5, len(display_primes))]
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
