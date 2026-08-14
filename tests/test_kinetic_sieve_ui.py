import pytest

from ui.kinetic_sieve import (
    CONFIRMED_PRIME,
    NEWLY_RESOLVED,
    RESOLVED_COMPOSITE,
    UNRESOLVED_CANDIDATE,
    build_kinetic_sieve_html,
)


def test_kinetic_html_uses_prime_lab_state_palette_and_terms():
    html = build_kinetic_sieve_html()

    assert CONFIRMED_PRIME in html
    assert UNRESOLVED_CANDIDATE in html
    assert NEWLY_RESOLVED in html
    assert RESOLVED_COMPOSITE in html

    assert "Confirmed prime" in html
    assert "Unresolved candidate" in html
    assert "Newly resolved composite" in html
    assert "Resolved composite" in html
    assert "first eliminating prime" in html


def test_kinetic_html_starts_before_prime_two_is_confirmed():
    html = build_kinetic_sieve_html()

    assert 'let simPosition = 1.55;' in html
    assert 'let processedThrough = 1;' in html
    assert 'id="latestPrime" class="metric-value">None yet<' in html
    assert 'id="primeCount" class="metric-value">0<' in html


def test_kinetic_html_contains_continuous_browser_animation_and_collision_logic():
    html = build_kinetic_sieve_html()

    assert "requestAnimationFrame(frame)" in html
    assert 'lastEvent.kind === "meeting"' in html
    assert "lastEvent.factors.includes(prime)" in html
    assert "meet at" in html
    assert "Math.ceil((simPosition + 1e-9) / prime) * prime" in html


def test_kinetic_html_uses_requested_runtime_configuration():
    html = build_kinetic_sieve_html(
        base_speed=2.0,
        maximum_value=12345,
    )

    assert '"baseSpeed": 2.0' in html
    assert '"maximumValue": 12345' in html


def test_kinetic_html_rejects_invalid_runtime_configuration():
    with pytest.raises(ValueError):
        build_kinetic_sieve_html(
            base_speed=0,
        )

    with pytest.raises(ValueError):
        build_kinetic_sieve_html(
            maximum_value=99,
        )
