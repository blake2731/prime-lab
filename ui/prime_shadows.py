import plotly.graph_objects as go
from plotly.colors import qualitative

from prime_lab.prime_shadows import (
    CONFIRMED_CODE,
    NON_CANDIDATE_CODE,
    TARGET_CODE,
    UNRESOLVED_CODE,
    PrimeShadow,
)


SPECIAL_COLORS = {
    TARGET_CODE: "#172033",
    CONFIRMED_CODE: "#008A7C",
    UNRESOLVED_CODE: "#2457E6",
    NON_CANDIDATE_CODE: "#E3E8EF",
}


def _state_label(code: int) -> str:
    if code == TARGET_CODE:
        return "Target prime"

    if code == CONFIRMED_CODE:
        return "Confirmed prime neighbor"

    if code == UNRESOLVED_CODE:
        return "Unresolved survivor"

    if code == NON_CANDIDATE_CODE:
        return "Not a prime candidate"

    return f"First eliminated by prime {code}"


def _observed_category_order(
    shadows: tuple[PrimeShadow, ...],
) -> tuple[int, ...]:
    observed = {
        code
        for shadow in shadows
        for code in shadow.state_codes
    }

    special_order = (
        TARGET_CODE,
        CONFIRMED_CODE,
        UNRESOLVED_CODE,
        NON_CANDIDATE_CODE,
    )

    ordered = [
        code
        for code in special_order
        if code in observed
    ]

    ordered.extend(
        sorted(
            code
            for code in observed
            if code > 0
        )
    )

    return tuple(ordered)


def _category_colors(
    categories: tuple[int, ...],
) -> tuple[str, ...]:
    prime_palette = qualitative.Dark24
    prime_index = 0
    colors: list[str] = []

    for code in categories:
        if code in SPECIAL_COLORS:
            colors.append(
                SPECIAL_COLORS[code]
            )

        else:
            colors.append(
                prime_palette[
                    prime_index
                    % len(prime_palette)
                ]
            )
            prime_index += 1

    return tuple(colors)


def _discrete_colorscale(
    colors: tuple[str, ...],
) -> list[list[float | str]]:
    if len(colors) == 1:
        return [
            [0.0, colors[0]],
            [1.0, colors[0]],
        ]

    scale: list[list[float | str]] = []
    count = len(colors)

    for index, color in enumerate(colors):
        lower = index / count
        upper = (index + 1) / count
        scale.append([lower, color])
        scale.append([upper, color])

    return scale


def build_shadow_heatmap(
    shadows: tuple[PrimeShadow, ...],
    title: str | None = None,
) -> go.Figure:
    """Render one or more prime centered sieve fingerprints."""

    if not shadows:
        raise ValueError(
            "at least one prime shadow is required"
        )

    reference_offsets = shadows[0].offsets

    if any(
        shadow.offsets != reference_offsets
        for shadow in shadows[1:]
    ):
        raise ValueError(
            "all prime shadows must use matching offsets"
        )

    categories = _observed_category_order(
        shadows
    )
    colors = _category_colors(
        categories
    )
    category_index = {
        code: index
        for index, code in enumerate(categories)
    }

    z = []
    hover = []

    for shadow in shadows:
        z_row = []
        hover_row = []

        for offset, value, code in zip(
            shadow.offsets,
            shadow.values,
            shadow.state_codes,
            strict=True,
        ):
            z_row.append(
                category_index[code]
            )

            hover_row.append(
                f"<b>Center prime {shadow.center_prime:,}</b>"
                f"<br>Offset {offset:+d}"
                f"<br>Integer {value:,}"
                f"<br>{_state_label(code)}"
            )

        z.append(z_row)
        hover.append(hover_row)

    row_labels = [
        str(shadow.center_prime)
        for shadow in shadows
    ]

    category_count = len(categories)
    zmax = max(
        category_count - 1,
        1,
    )

    figure = go.Figure()

    figure.add_trace(
        go.Heatmap(
            z=z,
            x=list(reference_offsets),
            y=row_labels,
            text=hover,
            zmin=0,
            zmax=zmax,
            colorscale=_discrete_colorscale(
                colors
            ),
            showscale=True,
            xgap=1,
            ygap=1,
            hovertemplate=(
                "%{text}"
                "<extra></extra>"
            ),
            colorbar={
                "title": "State",
                "tickmode": "array",
                "tickvals": list(
                    range(category_count)
                ),
                "ticktext": [
                    _state_label(code)
                    for code in categories
                ],
                "len": 0.9,
            },
        )
    )

    figure.add_vline(
        x=0,
        line={
            "color": "#172033",
            "width": 2,
        },
    )

    figure.update_layout(
        title=(
            {
                "text": title,
                "x": 0.01,
                "xanchor": "left",
            }
            if title
            else None
        ),
        height=(
            250
            if len(shadows) == 1
            else min(
                850,
                max(
                    360,
                    90 + 28 * len(shadows),
                ),
            )
        ),
        margin={
            "l": 70,
            "r": 210,
            "t": 55 if title else 30,
            "b": 60,
        },
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    figure.update_xaxes(
        title_text="Offset from center prime",
        showgrid=False,
        zeroline=False,
    )

    figure.update_yaxes(
        title_text=(
            "Center prime"
            if len(shadows) > 1
            else None
        ),
        autorange="reversed",
        showgrid=False,
    )

    return figure
