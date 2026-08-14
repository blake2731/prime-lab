import streamlit as st

from ui.kinetic_sieve import build_kinetic_sieve_html


st.set_page_config(
    page_title="Kinetic Sieve Lab",
    page_icon="∴",
    layout="wide",
)


st.title("Kinetic Sieve Lab")
st.caption(
    "Watch prime structure emerge as confirmed primes move through their multiples and meet at shared composite numbers."
)

st.info(
    "This experiment runs automatically. Each unresolved integer waits for the discovery frontier. "
    "If no earlier prime trajectory reaches that integer, it is confirmed prime and joins the motion. "
    "If one or more prime trajectories arrive, the integer is resolved as composite."
)

with st.expander(
    "How to read the motion",
    expanded=True,
):
    st.write(
        "A confirmed prime follows the exact rhythm of its multiples. Prime 2 reaches 4, 6, 8, 10, and so on; Prime 3 reaches 6, 9, 12, 15, and so on. "
        "The travel time between landings is proportional to the prime, so the visual timing is tied directly to divisibility."
    )

    st.write(
        "When trajectories share a multiple, they arrive at the same integer at the same time. "
        "For example, Prime 2 and Prime 3 meet at 6, 12, 18, and every later common multiple. "
        "Those meetings visualize factor overlap rather than an animation effect."
    )

    st.write(
        "Prime Lab keeps its existing ownership rule at the same time: a resolved composite belongs to its smallest prime factor, called the first eliminating prime. "
        "Other prime trajectories may still meet that composite because they are additional factors."
    )


st.iframe(
    build_kinetic_sieve_html(),
    width="stretch",
    height=655,
)

st.caption(
    "The browser renders only a sliding visible window while the mathematical frontier continues forward. "
    "This keeps the page lightweight enough to run continuously for long sessions without retaining every rendered cell."
)

with st.expander(
    "What to look for while it runs",
    expanded=False,
):
    st.markdown(
        """
1. **Prime emergence:** a candidate reaches the frontier without any earlier prime trajectory landing on it and becomes a confirmed prime.
2. **Shared multiples:** two or more prime trajectories meet at the same composite, revealing its distinct prime factors in real time.
3. **Repeating rhythms:** small primes create visibly frequent cycles while larger primes contribute progressively longer periods.
4. **Composite ownership:** even during a multi-prime meeting, the smallest factor remains the first eliminating prime.
5. **Changing density:** confirmed primes become less frequent as the frontier moves farther along the integers.
        """
    )

st.warning(
    "Kinetic Sieve Lab is an exact visualization of divisibility events, but visible patterns should still be treated as observations rather than mathematical claims. "
    "Patterns that look interesting can later be measured in Prime Lab instead of being inferred from appearance alone."
)
