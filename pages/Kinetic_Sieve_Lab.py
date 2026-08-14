import streamlit as st

from ui.kinetic_sieve import build_kinetic_sieve_html


st.set_page_config(
    page_title="Kinetic Sieve Lab",
    page_icon="∴",
    layout="wide",
)


st.title("Kinetic Sieve Lab")
st.caption(
    "Visualize prime discovery as synchronized divisibility trajectories moving through the integers."
)

st.info(
    "This experiment runs automatically. Each unresolved integer waits for the discovery frontier. "
    "If no earlier prime trajectory reaches that integer, it is confirmed prime and joins the motion. "
    "If one or more prime trajectories arrive, the integer is resolved as composite."
)

with st.expander(
    "Mathematical interpretation",
    expanded=True,
):
    st.write(
        "Each confirmed prime repeatedly travels from one multiple to the next. Prime 2 reaches 4, 6, 8, 10, and so on; Prime 3 reaches 6, 9, 12, 15, and so on. "
        "Travel time is proportional to the prime, so landing times remain tied directly to divisibility."
    )

    st.write(
        "The visible trajectory uses a half sine arch. If t measures progress from one multiple to the next, the vertical shape is proportional to sin(πt). "
        "Each trajectory therefore begins on the number row, reaches its highest point halfway through the interval, and returns exactly to the next multiple. "
        "π determines the geometry of the arch; it is not evidence of a causal relationship between π and prime distribution."
    )

    st.write(
        "When trajectories share a multiple, they arrive at the same integer at the same time. "
        "For example, Prime 2 and Prime 3 meet at 6, 12, 18, and every later common multiple. "
        "These meetings visualize exact factor overlap."
    )

    st.write(
        "A resolved composite is assigned to its smallest prime factor, called the first eliminating prime. "
        "Additional prime trajectories may still meet at that composite because they represent other prime factors."
    )


st.iframe(
    build_kinetic_sieve_html(),
    width="stretch",
    height=900,
)

st.caption(
    "The visible number row uses a sliding camera rather than continually adding rendered cells. "
    "The animation retains only a bounded session log, allowing long runs without unbounded growth of the rendered history or event table."
)

with st.expander(
    "Observable features",
    expanded=False,
):
    st.markdown(
        """
1. **Prime emergence:** a candidate reaches the frontier without any earlier prime trajectory landing on it and becomes a confirmed prime.
2. **Shared multiples:** two or more prime trajectories meet at the same composite, revealing its distinct prime factors in real time.
3. **Repeating periods:** small primes create frequent cycles while larger primes contribute progressively longer periods.
4. **Composite ownership:** during a multiple trajectory meeting, the smallest factor remains the first eliminating prime.
5. **Changing density:** confirmed primes become less frequent as the frontier moves farther along the integers.
6. **Event log:** confirmed prime events and shared meetings are retained in a bounded log that can be exported as CSV for separate analysis.
        """
    )

st.warning(
    "Kinetic Sieve Lab is an exact visualization of divisibility events. Visual structure should be treated as an observation until it is measured, reproduced, and compared with established number theoretic results."
)
