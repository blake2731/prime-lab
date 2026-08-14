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
    "Represent divisibility as synchronized circular phase, with one repeating cycle for each prime."
)

st.info(
    "For a prime p and integer n, the remainder n mod p can be normalized to one turn of a circle. "
    "The phase is (n mod p) / p and the corresponding angle is 2π(n mod p) / p. "
    "A return to phase zero means p divides n exactly."
)

with st.expander("Relationship to primality", expanded=True):
    st.write(
        "As n advances by one, every prime cycle advances by one residue step. A composite integer is reached when at least one relevant earlier prime cycle returns to phase zero. "
        "To prove that n is prime, it is sufficient to check prime cycles through √n. If none of those cycles is at zero, n has no possible smaller prime divisor."
    )
    st.write(
        "The cycle associated with n itself is not evidence that n is composite. For example, the Prime 5 cycle is at phase zero at n = 5, but 5 remains prime because no smaller relevant prime cycle divides it."
    )
    st.write(
        "When several prime cycles return to zero together, the event is the circular phase representation of the shared multiple meetings shown in Kinetic Sieve Lab."
    )

st.subheader("1. Inspect one integer state")
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
                "Select an integer and inspect the modular phase of the displayed prime cycles. "
                "The current ceiling of one trillion is a practical interface limit rather than a mathematical boundary."
            ),
        )
    )

with control_right:
    clock_count = int(
        st.slider(
            "Base prime cycles to display",
            min_value=3,
            max_value=12,
            value=8,
            help=(
                "Displays the first N prime cycles. Any additional phase zero divisor cycles are added automatically so the visualization includes the factors responsible for a composite classification."
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
    "Phase zero divisor cycles",
    "None" if not relevant_zeros else " · ".join(str(prime) for prime in relevant_zeros),
)
metric_four.metric(
    "Prime cycles required for proof",
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
        "Additional divisor cycle"
        + ("s " if len(extra_divisor_primes) != 1 else " ")
        + ", ".join(str(prime) for prime in extra_divisor_primes)
        + " were added automatically because they fall outside the selected base cycle set."
    )

st.caption(
    f"The clock panel visualizes {len(display_primes)} cycle{'s' if len(display_primes) != 1 else ''}. "
    f"The primality proof checks all {len(proof_primes):,} prime cycles through √n. "
    "Teal indicates a displayed prime cycle; amber emphasis is reserved for a cycle that is at phase zero and divides n."
)

st.plotly_chart(build_prime_clock_figure(states), width="stretch")

phase_rows = []
for state in states:
    if state.is_relevant_divisor:
        role = "Phase zero divisor"
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
            "Remainder": state.remainder,
            "Next zero": state.next_zero,
            "Steps to next zero": state.steps_to_next_zero,
            "Normalized phase": state.phase_fraction,
            "Angle degrees": state.angle_degrees,
            "Role": role,
        }
    )

phase_frame = pd.DataFrame(phase_rows)
future_states = [state for state in states if state.steps_to_next_zero > 0]
nearest_future = min(future_states, key=lambda state: (state.steps_to_next_zero, state.prime))

schedule_metric_1, schedule_metric_2 = st.columns(2)
schedule_metric_1.metric(
    "Nearest displayed zero crossing",
    f"Prime {nearest_future.prime} in {nearest_future.steps_to_next_zero} step{'s' if nearest_future.steps_to_next_zero != 1 else ''}",
)
schedule_metric_2.metric(
    "Phase signature width",
    f"{len(display_primes)} displayed prime cycles",
)

schedule_col, export_col = st.columns([4, 1])
with schedule_col:
    with st.expander("Prime cycle schedule", expanded=True):
        st.write(
            "Each row records the current phase position of one displayed prime cycle and the next integer at which that cycle returns to zero. "
            "This is the circular phase equivalent of the landing schedule in Kinetic Sieve Lab."
        )
        st.dataframe(
            phase_frame,
            width="stretch",
            hide_index=True,
            column_config={
                "Normalized phase": st.column_config.NumberColumn(format="%.6f"),
                "Angle degrees": st.column_config.NumberColumn(format="%.3f"),
            },
        )
        st.code(
            "Phase signature: ("
            + ", ".join(f"{state.prime}:{state.remainder}" for state in states)
            + ")",
            language=None,
        )
with export_col:
    st.download_button(
        "Download phase CSV",
        data=phase_frame.to_csv(index=False).encode("utf-8"),
        file_name=f"prime_phase_{current_integer}.csv",
        mime="text/csv",
        width="stretch",
    )

if selected_sync:
    st.caption(
        "Displayed cycles currently at phase zero: "
        + ", ".join(str(prime) for prime in selected_sync)
        + ". Exact zero crossings are distinct from prime cycles that are merely within the √n proof range."
    )

st.subheader("2. Two cycle phase projection")
st.write(
    "Two prime cycles can be represented as one point in a unit square. The horizontal coordinate is the normalized phase of one cycle and the vertical coordinate is the normalized phase of the other. "
    "As n advances, the point visits a finite sequence of joint states before repeating."
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
    "The shared zero state is their common multiple synchronization point. The projection is limited to base cycles so the entire repeating period remains lightweight."
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

st.subheader("3. Local phase rhythms")
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
    "Each trace is a normalized modular sawtooth. A return to phase zero is an exact multiple of that prime. Simultaneous returns to zero represent synchronization at a shared multiple."
)

with st.expander("Suggested experiments", expanded=False):
    st.markdown(
        """
1. Compare a prime integer with the composites immediately before and after it. Record which relevant cycles are closest to phase zero.
2. Compare n = 30, 60, 90, and 210 to examine multi prime synchronization events in both the clocks and the two cycle projection.
3. Compare different pairs of prime cycles and record how the joint repetition period changes.
4. Interpret prime gaps as intervals in which at least one relevant prime cycle reaches phase zero at every intermediate integer.
5. Compare phase signatures around distant primes and test whether apparent similarity persists after controlling for ordinary sieve structure.
        """
    )

with st.expander("Methods and limits", expanded=False):
    st.markdown(
        f"""
**Exact modular state.** Every displayed phase is computed directly from `n mod p`; no visual interpolation is used to classify divisibility.

**Proof versus display.** The clock panel intentionally shows only a small base set plus any additional divisor cycles needed to explain a composite. Primality classification still checks every prime through √n.

**Two cycle projection.** A pair of distinct prime cycles repeats after their product because the two moduli are coprime.

**Interface ceiling.** Integer input is capped at {MAX_INTEGER:,}. This is an engineering boundary for the current interactive implementation, not a mathematical limit of phase representation.

**Interpretation.** Phase space is a coordinate system for modular arithmetic. Similar looking phase signatures require quantitative comparison and controls for ordinary congruence structure before they can support a new claim.
        """
    )

st.warning(
    "Prime Phase Space is a coordinate representation of exact modular arithmetic. It does not imply that circles or π cause the distribution of primes. "
    "Its purpose is to expose periodic structure in a form that can be measured, compared, and tested."
)
