import plotly.graph_objects as go

from prime_lab.prime_gaps import (
    PrimeGapRecord,
    gap_frequency,
)


def _rolling_average(
    records: tuple[PrimeGapRecord, ...],
    window: int = 25,
) -> tuple[list[int], list[float]]:
    """Return a simple rolling mean for observed gap size."""

    if len(records) < window:
        return [], []

    x_values: list[int] = []
    averages: list[float] = []
    running_sum = sum(
        record.gap
        for record in records[:window]
    )

    x_values.append(
        records[window - 1].lower_prime
    )
    averages.append(
        running_sum / window
    )

    for index in range(window, len(records)):
        running_sum += records[index].gap
        running_sum -= records[index - window].gap
        x_values.append(
            records[index].lower_prime
        )
        averages.append(
            running_sum / window
        )

    return x_values, averages


def build_prime_gap_timeline(
    records: tuple[PrimeGapRecord, ...],
) -> go.Figure:
    """Plot confirmed prime gaps against the lower prime in each pair."""

    lower_primes = [
        record.lower_prime
        for record in records
    ]

    gaps = [
        record.gap
        for record in records
    ]

    log_scale = [
        record.log_scale
        for record in records
    ]

    hover_text = [
        (
            f"<b>{record.lower_prime:,} → {record.upper_prime:,}</b>"
            f"<br>Prime gap: {record.gap:,}"
            f"<br>ln({record.lower_prime:,}) = {record.log_scale:.2f}"
            f"<br>Gap / ln(p) = {record.normalized_gap:.2f}"
        )
        for record in records
    ]

    figure = go.Figure()

    figure.add_trace(
        go.Scatter(
            x=lower_primes,
            y=gaps,
            mode="markers",
            marker={
                "color": "#2457E6",
                "size": 6,
                "opacity": 0.72,
            },
            text=hover_text,
            name="Observed prime gap",
            hovertemplate=(
                "%{text}"
                "<extra></extra>"
            ),
        )
    )

    rolling_x, rolling_gap = _rolling_average(
        records
    )

    if rolling_x:
        figure.add_trace(
            go.Scatter(
                x=rolling_x,
                y=rolling_gap,
                mode="lines",
                line={
                    "color": "#243247",
                    "width": 2.5,
                },
                name="25 gap rolling average",
                hovertemplate=(
                    "Lower prime %{x:,}"
                    "<br>25 gap average %{y:.2f}"
                    "<extra></extra>"
                ),
            )
        )

    figure.add_trace(
        go.Scatter(
            x=lower_primes,
            y=log_scale,
            mode="lines",
            line={
                "color": "#AAB4C3",
                "width": 2,
                "dash": "dash",
            },
            name="ln(p) spacing scale",
            hovertemplate=(
                "Lower prime %{x:,}"
                "<br>ln(p) %{y:.2f}"
                "<extra></extra>"
            ),
        )
    )

    record_points = [
        record
        for record in records
        if record.is_local_record
    ]

    figure.add_trace(
        go.Scatter(
            x=[
                record.lower_prime
                for record in record_points
            ],
            y=[
                record.gap
                for record in record_points
            ],
            mode="markers",
            marker={
                "color": "#D97706",
                "size": 10,
                "symbol": "diamond",
            },
            text=[
                (
                    f"<b>New record within this range</b>"
                    f"<br>{record.lower_prime:,} → {record.upper_prime:,}"
                    f"<br>Gap {record.gap:,}"
                )
                for record in record_points
            ],
            name="New record gap",
            hovertemplate=(
                "%{text}"
                "<extra></extra>"
            ),
        )
    )

    figure.update_layout(
        height=500,
        margin={
            "l": 55,
            "r": 20,
            "t": 45,
            "b": 55,
        },
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "left",
            "x": 0,
        },
        hovermode="closest",
    )

    figure.update_xaxes(
        title_text="Lower prime p",
        showgrid=True,
        gridcolor="#E3E8EF",
        zeroline=False,
    )

    figure.update_yaxes(
        title_text="Gap to next confirmed prime",
        showgrid=True,
        gridcolor="#E3E8EF",
        zeroline=False,
        rangemode="tozero",
    )

    return figure


def build_gap_frequency_figure(
    records: tuple[PrimeGapRecord, ...],
) -> go.Figure:
    """Plot the frequency of each observed confirmed prime gap size."""

    frequencies = gap_frequency(
        records
    )

    gap_sizes = [
        gap
        for gap, _ in frequencies
    ]

    counts = [
        count
        for _, count in frequencies
    ]

    figure = go.Figure()

    figure.add_trace(
        go.Bar(
            x=gap_sizes,
            y=counts,
            marker={
                "color": "#2457E6",
            },
            hovertemplate=(
                "Gap %{x:,}"
                "<br>Occurrences %{y:,}"
                "<extra></extra>"
            ),
            name="Observed frequency",
        )
    )

    figure.update_layout(
        height=430,
        margin={
            "l": 55,
            "r": 20,
            "t": 35,
            "b": 55,
        },
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )

    figure.update_xaxes(
        title_text="Prime gap size",
        showgrid=False,
        zeroline=False,
        dtick=2,
    )

    figure.update_yaxes(
        title_text="Number of occurrences",
        showgrid=True,
        gridcolor="#E3E8EF",
        zeroline=False,
        rangemode="tozero",
    )

    return figure


def build_normalized_gap_figure(
    records: tuple[PrimeGapRecord, ...],
) -> go.Figure:
    """Plot each observed gap relative to the local logarithmic spacing scale."""

    lower_primes = [
        record.lower_prime
        for record in records
    ]

    ratios = [
        record.normalized_gap
        for record in records
    ]

    hover_text = [
        (
            f"<b>{record.lower_prime:,} → {record.upper_prime:,}</b>"
            f"<br>Gap: {record.gap:,}"
            f"<br>ln(p): {record.log_scale:.2f}"
            f"<br>Gap / ln(p): {record.normalized_gap:.2f}"
        )
        for record in records
    ]

    figure = go.Figure()

    figure.add_trace(
        go.Scatter(
            x=lower_primes,
            y=ratios,
            mode="markers",
            marker={
                "color": "#008A7C",
                "size": 6,
                "opacity": 0.72,
            },
            text=hover_text,
            name="Gap / ln(p)",
            hovertemplate=(
                "%{text}"
                "<extra></extra>"
            ),
        )
    )

    figure.add_hline(
        y=1.0,
        line={
            "color": "#AAB4C3",
            "width": 2,
            "dash": "dash",
        },
        annotation_text="gap = ln(p)",
        annotation_position="top right",
    )

    figure.update_layout(
        height=430,
        margin={
            "l": 55,
            "r": 20,
            "t": 35,
            "b": 55,
        },
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )

    figure.update_xaxes(
        title_text="Lower prime p",
        showgrid=True,
        gridcolor="#E3E8EF",
        zeroline=False,
    )

    figure.update_yaxes(
        title_text="Observed gap divided by ln(p)",
        showgrid=True,
        gridcolor="#E3E8EF",
        zeroline=False,
        rangemode="tozero",
    )

    return figure
