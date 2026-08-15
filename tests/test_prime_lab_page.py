from pathlib import Path

from streamlit.testing.v1 import AppTest


APP_SOURCE = Path("app.py").read_text(encoding="utf-8")


def test_baseline_lab_uses_committed_experiment_form():
    assert 'with st.form("prime_lab_experiment_form"' in APP_SOURCE
    assert '"Apply experiment"' in APP_SOURCE
    assert 'st.session_state["prime_lab_experiment"]' in APP_SOURCE


def test_baseline_lab_does_not_use_legacy_sieve_animation():
    assert "build_sieve_animation" not in APP_SOURCE


def test_baseline_lab_keys_visualization_to_committed_state():
    assert "experiment_token" in APP_SOURCE
    assert "prime_lab_chart_" in APP_SOURCE
    assert "uirevision=chart_key" in APP_SOURCE


def test_baseline_lab_includes_exact_inspection_and_exports():
    assert "Inspect one integer" in APP_SOURCE
    assert '"Download state CSV"' in APP_SOURCE
    assert '"Download filter CSV"' in APP_SOURCE


def test_baseline_lab_survives_applying_a_new_range():
    app = AppTest.from_file("app.py")
    app.run(timeout=15)

    assert not app.exception
    assert app.number_input[0].label == "Range start"
    assert app.number_input[1].label == "Range end"
    assert app.button[0].label == "Apply experiment"

    app.number_input[1].set_value(750)
    app.button[0].click().run(timeout=15)

    assert not app.exception
    assert app.session_state["prime_lab_experiment"]["end"] == 750
    assert any(
        metric.label == "Prime candidates" and metric.value == "749"
        for metric in app.metric
    )
